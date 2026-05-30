import urllib.request
import json
import re

test_cases_file = 'd:/drive/test_cases.txt'
results_file = 'd:/drive/test_results.txt'

with open(test_cases_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

history = []

with open(results_file, 'w', encoding='utf-8') as out_f:
    out_f.write('Test Results\n')
    out_f.write('=' * 50 + '\n\n')

    for line in lines:
        line = line.strip()
        match = re.match(r'^(\d+)\.\s+(.*)', line)
        if match:
            num = match.group(1)
            query = match.group(2)
            
            # Clear history if it's a new category
            if num in ['1', '11', '17', '25', '33', '38', '43', '48']:
                history = []
            
            print(f'Running test {num}: {query}')
            
            req_data = {
                'text': query,
                'history': history,
                'gps': {'latitude': 13.01, 'longitude': 80.23} if '13.01' in query or 'GPS' in query else None
            }
            
            req = urllib.request.Request(
                'http://127.0.0.1:8000/query',
                data=json.dumps(req_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    answer = res_data.get('response', 'No response')
                    
                    # Update history
                    history.append({'role': 'user', 'parts': [query]})
                    history.append({'role': 'model', 'parts': [answer]})
                    
                    out_f.write(f'Test {num}: {query}\n')
                    out_f.write(f'Answer: {answer}\n')
                    out_f.write('-' * 40 + '\n')
            except Exception as e:
                print(f'Error running test {num}: {e}')
                out_f.write(f'Test {num}: {query}\n')
                out_f.write(f'Error: {e}\n')
                out_f.write('-' * 40 + '\n')
print("Tests completed successfully!")
