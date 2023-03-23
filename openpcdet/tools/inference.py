import glob

import numpy as np
import redis
from config import cfgs
from pcdet.datasets import DatasetTemplate

redis_client = redis.Redis(
    host=cfgs.redis.get("host"), port=cfgs.redis.get("port"), password=cfgs.redis.get("password")
)


class ServiceDataset(DatasetTemplate):
    def __init__(
        self, dataset_cfg, class_names, training=False, root_path=None, logger=None, ext=".bin"
    ):
        """
        Args:
            root_path:
            dataset_cfg:
            class_names:
            training:
            logger:
        """
        super().__init__(
            dataset_cfg=dataset_cfg,
            class_names=class_names,
            training=training,
            root_path=root_path,
            logger=logger,
        )
        self.root_path = root_path
        self.ext = ext
        data_file_list = (
            glob.glob(str(root_path / f"*{self.ext}"))
            if self.root_path.is_dir()
            else [self.root_path]
        )

        data_file_list.sort()
        self.sample_file_list = data_file_list

    def __len__(self):
        return len(self.sample_file_list)

    def __getitem__(self, index):
        if self.ext == ".bin":
            points = np.fromfile(self.sample_file_list[index]).reshape(-1, 4)
            points = np.delete(points, np.where(points[:, 2] <= -1.7), axis=0)
        elif self.ext == ".npy":
            points = np.load(self.sample_file_list[index])
        elif self.ext == "redis":
            pcd = redis_client.rpop(cfgs.redis.get("host"))
            points = np.frombuffer(pcd).reshape(-1, 4)
            points = np.delete(points, np.where(points[:, 2] <= -1.7), axis=0)
        else:
            raise NotImplementedError

        input_dict = {
            "points": points,
            "original_points": points,
            "frame_id": index,
        }
        data_dict = self.prepare_data(data_dict=input_dict)
        return data_dict
