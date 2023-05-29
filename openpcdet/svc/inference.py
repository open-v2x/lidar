import json
import math
from typing import Dict

import pandas as pd
import torch
from config import cfgs
from pcdet.config import cfg as config, cfg_from_yaml_file
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils
from udp_dataset import UDPDataset


class Inference:

    # initialize model
    def __init__(self):
        self.cfg_file = cfgs.cfg_file.get("cfg_file")
        self.ckpt = cfgs.ckpt.get("ckpt")
        self.logger = common_utils.create_logger()
        self.cfg = cfg_from_yaml_file(self.cfg_file, config)
        self.init_dataset = UDPDataset(
            dataset_cfg=self.cfg.DATA_CONFIG,
            class_names=self.cfg.CLASS_NAMES,
            training=False,
            logger=self.logger,
        )
        self.model = build_network(
            model_cfg=self.cfg.MODEL,
            num_class=len(self.cfg.CLASS_NAMES),
            dataset=self.init_dataset,
        )
        self.model.load_params_from_file(filename=self.ckpt, logger=self.logger, to_cpu=False)
        self.model.cuda()
        self.model.eval()
        self.lidar_info: Dict[str, dict] = {
            "lidar1": {
                "bias_x": 888,
                "bias_y": 499,
                "rotation": 0.0,
                "reverse": True,
                "scale": 1.2,
                "focal_length": 25,
            }
        }

    async def run(self, points):
        with torch.no_grad():
            self.logger.info(
                "-----------------Inference result of OpenPCDet-------------------------"
            )

            udp_dataset = UDPDataset(
                dataset_cfg=self.cfg.DATA_CONFIG,
                class_names=self.cfg.CLASS_NAMES,
                training=False,
                logger=self.logger,
                points=points,
            )
            data_dict = udp_dataset["data_dict"]
            data_dict = udp_dataset.collate_batch([data_dict])
            load_data_to_gpu(data_dict)
            pred_dicts, _ = self.model.forward(data_dict)

            # filter out low score bboxes
            if cfgs.score_thr.get("score_thr") > 0:
                inds = pred_dicts[0]["pred_scores"] > cfgs.score_thr.get("score_thr")
                pred_dicts[0]["pred_boxes"] = pred_dicts[0]["pred_boxes"][inds]
                # pred_dicts[0]["pred_scores"] = pred_dicts[0]["pred_scores"][inds]
                pred_dicts[0]["pred_labels"] = pred_dicts[0]["pred_labels"][inds]

            lidar_points = pred_dicts[0]["pred_boxes"].cpu().numpy()
            # 将NumPy数组转换为DataFrame
            df = pd.DataFrame(lidar_points, columns=["x", "y", "z", "dx", "dy", "dz", "angle"])
            df.apply(self.convert_for_visual, args=("lidar1",), axis=1)
            pixel_points = df.iloc[:, [0, 1, 6]].values.tolist()

            bbox_data = {
                "bboxes": pixel_points,
                # "scores": pred_dicts[0]["pred_scores"].cpu().numpy().tolist(),
                "labels": pred_dicts[0]["pred_labels"].cpu().numpy().tolist(),
            }
            result = json.dumps(bbox_data)
            self.logger.info("Inference done.")
            return result

    def convert_for_visual(self, frame, lidar_id) -> None:
        """Coordinate translation and rotation."""
        k = -1 if self.lidar_info[lidar_id]["reverse"] else 1
        frame["x"] = (
            k * frame["x"] * self.lidar_info[lidar_id]["focal_length"] / frame["z"]
            + self.lidar_info[lidar_id]["bias_x"]
        )
        frame["y"] = (
            frame["y"] * self.lidar_info[lidar_id]["focal_length"] / frame["z"]
            + self.lidar_info[lidar_id]["bias_y"]
        )
        frame["x"] = frame["x"] / self.lidar_info[lidar_id]["scale"]
        frame["y"] = frame["y"] / self.lidar_info[lidar_id]["scale"]
