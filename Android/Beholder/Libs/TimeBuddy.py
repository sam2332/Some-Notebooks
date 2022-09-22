class TimeBuddy:
    time = 0

    def __init__(self, unixTimestamp):
        self.time = unixTimestamp

    @staticmethod
    def From_Months(months):
        return TimeBuddy.From_Days(months * 30)

    @staticmethod
    def From_Days(days):
        return TimeBuddy.From_Hours(days * 24)

    @staticmethod
    def From_Hours(hours):
        return TimeBuddy.From_Minutes(hours * 60)

    @staticmethod
    def From_Minutes(minutes):
        return TimeBuddy.From_Seconds(minutes * 60)

    @staticmethod
    def From_Seconds(seconds):
        return seconds * 1000

    @staticmethod
    def From_Milliseconds(milliseconds):
        return milliseconds

    @classmethod
    def Build(cls, months=0, days=0, hours=0, minutes=0, seconds=0, milliseconds=0):
        return cls(
            TimeBuddy.From_Days(days)
            + TimeBuddy.From_Hours(hours)
            + TimeBuddy.From_Minutes(minutes)
            + TimeBuddy.From_Seconds(seconds)
            + TimeBuddy.From_Milliseconds(milliseconds)
        )

    def __gt__(self, other):
        return other.time > self.time

    def __lt__(self, other):
        return other.time < self.time

    def __eq__(self, other):
        return other.time == self.time