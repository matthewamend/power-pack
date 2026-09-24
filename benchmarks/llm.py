from openai import OpenAI

from power_pack import Acquisition, NIDaqConfig, RunReader

API_URL = "http://localhost:8080"
API_KEY = "..."

PROMPT = """
    Generate an SVG of a pelican riding a bicycle
"""


def main():
    config = NIDaqConfig(2000, 1000, "pelican.hdf5")

    acq = Acquisition("Pelican Bicycle SVG Benchmark", config)

    acq.start()

    try:
        client = OpenAI(api_key=API_KEY, base_url=API_URL)

        result = client.responses.create(
            model="",
            input=PROMPT,
        )

        print(result.output_text)
    finally:
        acq.stop()

    reader = RunReader("pelican.hdf5")

    reader.make_csv_files()

    reader.plot_all()


if __name__ == "__main__":
    main()
