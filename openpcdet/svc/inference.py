import json

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

            bbox_data = {
                "bboxes": pred_dicts[0]["pred_boxes"].cpu().numpy().tolist(),
                # "scores": pred_dicts[0]["pred_scores"].cpu().numpy().tolist(),
                "labels": pred_dicts[0]["pred_labels"].cpu().numpy().tolist(),
            }
            result = json.dumps(bbox_data)
            self.logger.info("Inference done.")
            return result
