class Util:
    def __init__(self, file_name):
        self.file_name = file_name
        self.logs = {
            'TIMESTAMP': [],
            'LEVEL': [],
            'MODULE': [],
            'MESSAGE': []
        }

    def __str__(self):
        return f"LogFile('{self.file_name}') | Records: {len(self.logs['LEVEL'])}"

    def load_file(self):
        try:
            with open(self.file_name) as log:
                print("File Found")
                return log.readlines()
        except FileNotFoundError as e:
            print("Error:", e)
            return []

    def parse_records(self):
        lines = self.load_file()

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 4:
                continue

            self.logs["TIMESTAMP"].append(parts[0])
            self.logs["LEVEL"].append(parts[1])
            self.logs["MODULE"].append(parts[2])
            self.logs["MESSAGE"].append(" ".join(parts[3:]))
