class util:

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