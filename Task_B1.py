logs = {
    'TIMESTAMP' : [],
    'LEVEL' : [],
    'MODULE' : [],
    'MESSAGE' : []
}

INFO  = 0b0001
WARN  = 0b0010
ERROR = 0b0100

LEVEL_FLAGS = {
    "INFO": INFO,
    "WARN": WARN,
    "ERROR": ERROR
}

IMPORTANT_LEVELS = WARN | ERROR

print("Enter the full name of log file(with extension)")

file_name = input()
print("is your file :", file_name)

with open(file_name ,'r') as log:
    lines = log.readlines()
    
    for line in lines:
        parts= line.strip().split()

        timestamp = parts[0]
        level = parts[1]
        module = parts[2]
        message = " ".join(parts[3:])
        
        logs["TIMESTAMP"].append(timestamp)
        logs["LEVEL"].append(level)
        logs["MODULE"].append(module)
        logs["MESSAGE"].append(message)

        level_flag = LEVEL_FLAGS.get(level, 0)

        if level_flag & IMPORTANT_LEVELS:
            print("IMPORTANT LOG FOUND:")
            print(timestamp, level, module, message)


    print("parsing complete")