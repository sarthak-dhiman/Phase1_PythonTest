from abc import ABC , abstractmethod
import copy

class BaseProcessor(ABC):

    @abstractmethod
    def Load_file(self):
        pass
    
    @abstractmethod
    def parse_records(self):
        pass

    @abstractmethod
    def calculate_stats(self):
        pass
                
    @abstractmethod
    def generate_report(self):
        pass

class LogFile(BaseProcessor):

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

    
    
    def Load_file(self):
        print("Enter the Log File Name or directory")
        print("File name imported")
        try:
            with open(self.file_name) as log:
               print("File Found")
               lines = log.readlines()
               return lines
        except FileNotFoundError as e :
            print("Error :" , e)
            return []
        
    
    def parse_records(self):
        
        lines = self.Load_file()

        for line in lines:
            parts= line.strip().split()

            timestamp = parts[0]
            level = parts[1]
            module = parts[2]
            message = " ".join(parts[3:])
        
            self.logs["TIMESTAMP"].append(timestamp)
            self.logs["LEVEL"].append(level)
            self.logs["MODULE"].append(module)
            self.logs["MESSAGE"].append(message)


    def calculate_stats(self):
        return {}

    def generate_report(self):
       pass
 
class UserAnalytics(BaseProcessor):

    def __init__(self, logs):
        self.logs = logs
    
    def calculate_stats(self):
        print("Notes down the occurance of each [LEVEL] code")
        stats = {
            'ERROR' : 0 ,
            'INFO' : 0 ,
            'WARN' : 0 ,
            'INVALID' : 0
            }
        for lvl in self.logs['LEVEL']:
            match lvl:
                case 'ERROR':
                    stats['ERROR'] += 1
                case 'INFO':
                    stats['INFO'] += 1
                case 'WARN':
                    stats['WARN'] += 1
                case _:
                    stats['INVALID'] +=1
        return stats
    
    def generate_report(self):
        stats = self.calculate_stats()
        print(stats)
        for k,v in stats.items():
            print(f"{k} occured : {v}")
    
    def Load_file(self):
        return super().Load_file()
    def parse_records(self):
        return super().parse_records()

if __name__ == "__main__":
    lf = LogFile("log.txt")
    print(lf)

    lf.parse_records()

    def mutate_logs(log_dict):
        log_dict['LEVEL'].append("DEBUG")

    lf.logs['LEVEL'].append("INFO")
    mutate_logs(lf.logs)

    shallow_copy = copy.copy(lf)
    shallow_copy.logs['LEVEL'].append("WARN")

    deep_copy = copy.deepcopy(lf)
    deep_copy.logs['LEVEL'].append("ERROR")

    analytics = UserAnalytics(lf.logs)
    analytics.generate_report()