from rich.console import Console

console = Console()

def main():
    console.print("Config Tool", style="bold red")

# TODO: - If config.yml exist ask to load it or create new.
#         - If new, ask file name. If file exists, ask to overwrite.
#         - If load, show file structure and allow users to navigate over fields and edit.

# TODO: QUESTIONNAIRE. Each field contains a description.
# - Integration name. Text input.
# - Run as a service. Binary input (yes or no).
# - IF run as a service YES:
#   - Cron interval in minutes. Natural mumber input (1-MAX).
# - IF run as a service NO:
#   - Service schedule:
#     - hour. Either ALL or list of increasing numbers in range (0, 23).
#     - minute. Either ALL or list of increasing numbers in range (0, 59).
# - Number of instances to create. Number 1 to MAX.
# - For each instance:
#   - Instance name. Text input (valid YAML string).
#   - Token URL. Formatted text input (valid URL).
#   - Auth type. List input ("User-Pass flow", "JWT flow")
#   - Auth attributes (type dependent). Text input.
#   - Cache enabled. Binary input (yes or no).
#   - IF cache enabled YES:
#     - Redis config attributes. Mixed input.
#   - (optional) API version. Formatted text input (integer "." integer).
#   - (optional) auth env prefix. Text input.
#   - (optional) date field. Text input (valid SF attribute name).
#   - (optional) generation interval. List input ("Daily", "Hourly")
#   - (optional) time lag minutes. Number (0-MAX).
#   - (optional) Queries. List of query objects (see "Queries" later).
#   - (optional) Logs enabled. Binary (yes or no).
#   - (optional) Limits.
#     - (optional) Limits API version. Formatted text input (integer "." integer).
#     - (optional) Limits names. List of names. Text input each.
#     - (optional) Limits event type. Text input.
#   - (optional) labels. List of key-value pairs. Text input.
# - Queries. List of query objects. Each object:
#   - query. Text input.
#   - (optional) timestamp attr. Text input.
#   - (optional) rename timestamp. Text input.
#   - (optional) api_ver. Formatted text input (integer "." integer).
#   - (optional) env. Env object:
#     - end_date. Text input.
#     - start_date. Text input.

# TODO: catch CTRL+C and store a backup of the ongoing config.

if __name__ == "__main__":
    main()
