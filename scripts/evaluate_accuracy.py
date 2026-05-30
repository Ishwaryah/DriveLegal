import os
import re
import sys
import codecs

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
import urllib.request

results_file = 'd:/drive/test_results.txt'
expected_file = 'd:/drive/test_cases_answers.txt'

def parse_expected(filepath):
    expected_answers = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match lines like "1. What is..." followed by "   - Expected Answer: ..."
    pattern = re.compile(r'(\d+)\.\s+.*?\n\s+-\s+Expected Answer:\s*(.*?)(?=\n\d+\.|\n\n|\Z)', re.DOTALL)
    matches = pattern.findall(content)
    for match in matches:
        expected_answers[match[0]] = match[1].strip()
    return expected_answers

def parse_results(filepath):
    results = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return results
        
    pattern = re.compile(r'Test (\d+):.*?\nAnswer: (.*?)(?=\n-{40})', re.DOTALL)
    matches = pattern.findall(content)
    for match in matches:
        results[match[0]] = match[1].strip()
    return results

def main():
    expected = parse_expected(expected_file)
    results = parse_results(results_file)
    
    if not results:
        print("No results found yet.")
        return

    correct_count = 0
    total_evaluated = 0
    
    print("Evaluating accuracy...")
    print("="*50)
    
    for num, expected_ans in expected.items():
        if num in results:
            actual_ans = results[num]
            total_evaluated += 1
            
            # Simple keyword matching for evaluation (we'll look for key numbers/fines)
            # Find all numbers (like 1000, 500, etc) in expected
            key_numbers = re.findall(r'\b\d+\b', expected_ans)
            
            # Remove small numbers like sections if possible, but let's just check if the main numbers exist in actual
            # A very simple heuristic: if any key number from expected is in actual, we consider it a hit (or partially correct)
            # For a more robust check, we could use Ollama, but let's do a basic check first.
            
            is_correct = False
            if any(num in actual_ans for num in key_numbers) and len(key_numbers) > 0:
                is_correct = True
            elif "decline" in expected_ans.lower() and ("sorry" in actual_ans.lower() or "cannot" in actual_ans.lower() or "traffic" in actual_ans.lower()):
                is_correct = True
                
            if is_correct:
                correct_count += 1
                
            print(f"Test {num}: {'PASS' if is_correct else 'FAIL'}")
            if not is_correct:
                print(f"  Expected: {expected_ans}")
                print(f"  Actual excerpt: {actual_ans[:100]}...")
                
    accuracy = (correct_count / total_evaluated) * 100 if total_evaluated > 0 else 0
    print("="*50)
    print(f"Total Evaluated: {total_evaluated}")
    print(f"Passed: {correct_count}")
    print(f"Accuracy: {accuracy:.2f}%")

if __name__ == "__main__":
    main()
