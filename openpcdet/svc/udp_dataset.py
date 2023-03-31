from pcdet.datasets import DatasetTemplate


class UDPDataset(DatasetTemplate):
    def __init__(self, dataset_cfg, class_names, training=False, logger=None, points=None):
        """
        Args:
            root_path:
            dataset_cfg:
            class_names:
            training:
            logger:
            points:
        """
        super().__init__(
            dataset_cfg=dataset_cfg,
            class_names=class_names,
            training=training,
            logger=logger,
        )
        self.points = points

    def __getitem__(self, index):
        input_dict = {
            "points": self.points,
            "frame_id": index,
        }
        data_dict = self.prepare_data(data_dict=input_dict)
        return data_dict


# parse splited pcd data received from udp
class DataParse:
    def __init__(
        self,
    ):
        self.data_dict = {}

    def parse(self, addr, udp_pcd):
        ip = addr[0]
        if udp_pcd == b"clear":
            self.data_dict[ip].clear()
            return
        if ip not in self.data_dict:
            self.data_dict[ip] = list()
        self.data_dict[ip].append(udp_pcd)
        if len(self.data_dict[ip]) == 180:
            data = b"".join(self.data_dict[ip])
            self.data_dict[ip].clear()
            return data
