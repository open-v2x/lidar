import argparse
import json
from pathlib import Path
from typing import Dict

import torch
import uvicorn
from config import cfgs
from fastapi import FastAPI, WebSocket
from fastapi_utils.tasks import repeat_every
from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils
from starlette.websockets import WebSocketDisconnect
from tools.inference import ServiceDataset
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, list] = {}

    async def connect(self, websocket: WebSocket, ip: str):
        await websocket.accept()
        if ip not in self.active_connections:
            self.active_connections[ip] = []

        self.active_connections[ip].append(websocket)

    def disconnect(self, websocket: WebSocket, ip: str):
        if ip in self.active_connections:
            if websocket in self.active_connections[ip]:
                self.active_connections[ip].remove(websocket)
            if not self.active_connections[ip]:
                self.active_connections.pop(ip)

    async def send_personal_message(self, message: list, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message, ip: str):
        for connection in self.active_connections[ip]:
            try:
                await connection.send_json(message)
            except (ConnectionClosedError, ConnectionClosedOK, WebSocketDisconnect):
                self.disconnect(connection, ip)


manager = ConnectionManager()


@app.get("/")
async def get():
    return {"test": "test"}


@app.websocket("/ws/{ip}")
async def websocket_endpoint(websocket: WebSocket, ip: str):
    await manager.connect(websocket, ip)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, ip)


def parse_config():
    parser = argparse.ArgumentParser(description="arg parser")
    parser.add_argument(
        "--cfg_file",
        type=str,
        default="cfgs/custom_models/centerpoint.yaml",
        help="specify the config for inference service",
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default="inference_data",
        help="specify the point cloud data file or directory",
    )
    parser.add_argument(
        "--ckpt",
        type=str,
        default="../ckpt/checkpoint_centerpoint_2100.pth",
        help="specify the pretrained model",
    )
    parser.add_argument("--score-thr", type=float, default=0.3, help="bbox score threshold")
    parser.add_argument(
        "--ext",
        type=str,
        default="redis",
        help="specify the extension of your point cloud data file",
    )

    args = parser.parse_args()

    cfg_from_yaml_file(args.cfg_file, cfg)

    return args, cfg


# load model
args, cfg = parse_config()
logger = common_utils.create_logger()
logger.info("-----------------Inference result of OpenPCDet-------------------------")
init_dataset = ServiceDataset(
    dataset_cfg=cfg.DATA_CONFIG,
    class_names=cfg.CLASS_NAMES,
    training=False,
    root_path=Path("data"),
    ext=".bin",
    logger=logger,
)
model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=init_dataset)
model.load_params_from_file(filename=args.ckpt, logger=logger, to_cpu=False)
model.cuda()
model.eval()


@app.on_event("startup")
@repeat_every(seconds=0.1)
async def inference():
    if manager.active_connections.keys():
        with torch.no_grad():
            service_dataset = ServiceDataset(
                dataset_cfg=cfg.DATA_CONFIG,
                class_names=cfg.CLASS_NAMES,
                training=False,
                root_path=Path(args.data_path),
                ext=args.ext,
                logger=logger,
            )
            data_dict = service_dataset["data_dict"]
            points = data_dict["original_points"]
            data_dict = service_dataset.collate_batch([data_dict])
            load_data_to_gpu(data_dict)
            pred_dicts, _ = model.forward(data_dict)

            # filter out low score bboxes for visualization
            if args.score_thr > 0:
                inds = pred_dicts[0]["pred_scores"] > args.score_thr
                pred_dicts[0]["pred_boxes"] = pred_dicts[0]["pred_boxes"][inds]
                pred_dicts[0]["pred_labels"] = pred_dicts[0]["pred_labels"][inds]
            logger.info("Inference done.")

            bbox_data = {
                "points": points.tolist(),
                "bboxes": pred_dicts[0]["pred_boxes"].cpu().numpy().tolist(),
                "scores": pred_dicts[0]["pred_scores"].cpu().numpy().tolist(),
                "labels": pred_dicts[0]["pred_labels"].cpu().numpy().tolist(),
            }
            result = json.dumps(bbox_data)
            for ip in manager.active_connections.keys():
                await manager.broadcast(result, ip)


if __name__ == "__main__":
    uvicorn.run(app=app, host=cfgs.websocket.get("host"), port=cfgs.websocket.get("port"))
