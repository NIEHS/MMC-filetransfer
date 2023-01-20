from MMC.lib.session import Session, filter_sessions, load_session_from_file

def find_sessions(group:str='*',project:str='*',session:str='*',details=False):
    sessions = filter_sessions(group,project,session)
    print(f'Found {len(sessions)} sessions')
    print('#'*40)
    for session in sessions:
        if  not details:
            print(session.name)
            continue
        _, session_obj = load_session_from_file(session.name)
        print(session_obj.to_string())
        print('#'*40)

def export(output:str, group:str='*',project:str='*',session:str='*'):
    sessions = filter_sessions(group,project,session)
    print(f'Found {len(sessions)} sessions')
    if output.endswith('.csv'):
        with open(output, 'w') as f:
            f.write(Session.csv_keys_string())
            for session in sessions:
                _, session_obj = load_session_from_file(session.name)
                f.write(session_obj.csv_string())          

    