import pandas as pd

from repeat import User, Application, TimeInterval


class RepeatTwin:
    def __init__(self, api_key, project_id, interval_sec):
        self.api_key = api_key
        self.project_id = project_id
        self.interval_sec = interval_sec

        self.user = User(self.api_key)
        self.app = Application(self.user)

        self.set_time_interval(self.interval_sec)

    def set_time_interval(self, interval_sec):
        self.interval_sec = interval_sec

        self.t_interval = TimeInterval(
            start=0,
            end=self.interval_sec * 1000
        )

        self.model = self.app.get_exploration_model(
            self.project_id,
            self.t_interval
        )

    def run_model(self, thermal_res, temp_batt, current, soc_init):
        variables = pd.Series({
            "thermalRes": thermal_res,
            "tempInit": temp_batt,
            "current": current,
            "SOCInit": soc_init
        }, dtype=float)

        with self.model as md:
            md.run(variables)

            temperature_result = md.get_results("tempResult")
            soc_result = md.get_results("SOCResult")

        return temperature_result, soc_result