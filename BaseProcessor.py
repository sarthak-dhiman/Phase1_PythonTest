from LogFile import Util
from UserAnalytics import util
import copy

if __name__ == "__main__":
    
    print("Enter the file name or directory")
    file_name = input()
    
    lf = Util(file_name)
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

    analytics = util(lf.logs)
    analytics.generate_report()
