logs = {
    'TIMESTAMP' : [],
    'LEVEL' : [],
    'MODULE' : [],
    'MESSAGE' : []
    }
error_list ={
    'TIMESTAMP' : [],
    'LEVEL' : [],
    'MODULE' : [],
    'MESSAGE' : []
}

def file_checking():
    print("Enter the Log File Name or directory")
    file_name = input()

    try:
        with open(file_name) as log:
            print("File Found")
            lines = log.readlines()
            return lines
    except FileNotFoundError as e :
        print("Error :" , e)
        with open("errors_task_C1.txt", "a+") as ef:
            ef.write(f"\nFile path error - {e}")
        
    
def log_segregation():
        
    lines = file_checking()

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
        
        if level == "ERROR":
            error_list["TIMESTAMP"].append(timestamp)
            error_list["LEVEL"].append(level)
            error_list["MODULE"].append(module)
            error_list["MESSAGE"].append(message)

            log_entry = f"{timestamp} {level} {module} {message}\n"

            with open("error_logs_C1.txt", "a+") as le:
                le.write(log_entry)

    print("logs and errors parsed")   

    return logs  
def log_printing():
    print(log_segregation())

print("Log management system")
print('select 1 for log segregation , 2 for file checking , 3 for log printing')
choice = int(input())
try:
    if choice < 0 or choice > 3:
        raise ValueError(f"invalid choice : {choice}")
except ValueError as e:
    print("Error:",e)
    with open("errors_task_C1.txt", "a+") as ef:
        ef.write(f"\ninvalid choice error - {e}")

match choice:
    case 1 :
        log_segregation()
    case 2 :
        file_checking()
    case 3 :
        log_printing()