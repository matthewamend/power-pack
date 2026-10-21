import time
import numpy as np

import longcot  #only new implemnetation
from openai import OpenAI #SENDSTO MODEL
from power_pack import Acquisition, NIDaqConfig, RunReader

API_URL = "http://localhost:8080/v1"
API_KEY = "..."
#Ithink the code requires a password?
qnum = 2  # change to 50 after the test run works

#local host talks to itself
# IF PORTS DONT MATCH, code cant find the server ( change it to match llama server


def main():
    questions = longcot.load_questions(domain="logic", difficulty="easy")[:qnum] #loaded from the longcot git
    client = OpenAI(api_key=API_KEY, base_url=API_URL, timeout=3600) #sets up connection to the ai model

    config = NIDaqConfig(2000, 1000, "longcot.hdf5")
    acq = Acquisition("LongCoT Benchmark", config)  #creates the power recorder using those settings

    marks = []  # when each question starts, so it shows as a line on the graph
    results = []  # saves each question's info

    # STEP 1: start measuring power
    acq.start()
    start = time.time()
    try:
        # STEP 2: wait 5 seconds to measure idle power
        time.sleep(5)

        # STEP 3: ask the AI each question
        for q in questions:
            marks.append(time.time() - start)
            t_start = time.time()  # question started
            result = client.chat.completions.create(
                model="",
                messages=[{"role": "user", "content": q.prompt}],  # q sent
                max_tokens=16384,
            )
            t_end = time.time()  # question finished
            answer = result.choices[0].message.content or ""
            tokens = result.usage.completion_tokens
            try:
                correct = longcot.verify(q, answer)  # is answer right or wrong
            except Exception:
                correct = "error"
            print(q.question_id, "tokens:", tokens, "correct:", correct)
            results.append((q.question_id, tokens, t_start, t_end))
    finally:
        # STEP 4: stop measuring power
        acq.stop()

    # STEP 5: save all data and make graphs
    reader = RunReader("longcot.hdf5")
    reader.make_csv_files("longcot-")
    reader.plot_all("longcot-", vertical_asymptotes=marks)

    # STEP 6: energy used during each question
    daq_start = float(reader.f.attrs["start_time"])  # when the DAQ started recording
    total_watts = sum(reader.dataframe(name).sum(axis=1).to_numpy()
                      for name, _ in reader._component_groups())  # all parts added together
    times = np.arange(len(total_watts)) / reader.sample_rate  # seconds for each reading
    for qid, tokens, t_start, t_end in results:
        during = (times >= t_start - daq_start) & (times <= t_end - daq_start)  # readings during this question
        energy = total_watts[during].sum() / reader.sample_rate  # watts x seconds = joules
        print(qid, "energy:", round(energy, 1), "J", "J/token:", round(energy / max(tokens, 1), 3))


if __name__ == "__main__":
    main()