import sys
import os
import re
import beautifulData as bd

pypricing_directory = os.path.expanduser("~/ArfimaTools/pypricing")
sys.path.insert(1, pypricing_directory)
try:
    from .underlyings import *  # (Relative) import needed for the workspace. In this case __package__ is pypricing.data
except (ImportError, ModuleNotFoundError, ValueError):
    from data.underlyings import *  # (Absolute) local import
try:
    from ..pricing.discount_curves import *  # Import needed for the workspace. In this case we need the parent package since discount curves

    # is in a different subpackage (pricing)
except (ImportError, ModuleNotFoundError, ValueError):
    from pricing.discount_curves import *  # (Absolute) local import
try:
    from .calendars import *
except (ImportError, ModuleNotFoundError, ValueError):
    from data.calendars import *
try:
    from . import specs as specs  # (Change name?)
except (ImportError, ModuleNotFoundError, ValueError):
    import data.specs as specs
try:
    from ..pricing import (
        functions as afsfun,
    )  # (Relative) import needed for the workspace. In this case __package__ is 'pypricing.data'
except (ImportError, ModuleNotFoundError, ValueError):
    import pricing.functions as afsfun  # (Absolute) local import. In this case __package__ is 'data'
try:
    from ..pricing.implied_volatility import (
        VolatilitySmile,
        VolatilitySurface,
        VolatilitySurfaceDelta,
    )  # (Relative) import needed for the workspace. In this case __package__ is 'pypricing.data'
except (ImportError, ModuleNotFoundError, ValueError):
    from pricing.implied_volatility import (
        VolatilitySmile,
        VolatilitySurface,
        VolatilitySurfaceDelta,
    )  # (Absolute) local import. In this case __package__ is 'data'

databases_path = os.path.expanduser("~/ArfimaTools/Databases/")


ibor_names = {
    "EUR": "EURIBOR curve",  # https://strata.opengamma.io/indices/#:~:text=calendar%20data%20available.-,Ibor%20Indices%3A,-An%20Ibor%20index
    "USD": "USD LIBOR curve",
    "JPY": "Yen LIBOR curve",
    "GBP": "Sterling LIBOR curve",
    "CNY": "Chinese Yuan LIBOR curve",
    "CHF": "Swiss Franc LIBOR curve",
    "EUR ISDA": "ISDA Euro curve",
    "USD ISDA": "ISDA US Dollar curve",
}

ois_names = {
    "EONIA": "EONIA Overnight Interest rate Swap curve (Euro zone)",
    "SOFR": "SOFR Overnight Interest rate Swap curve (USA)",
    "SONIA": "SONIA Overnight Interest rate Swap curve (UK)",
}

swi_names = {
    "EUSWI": "Euroarea HICP inflation swap curve",
    "USSWI": "US HICP inflation swap curve",
    "BPSWIT": "UK HICP inflation swap curve",
}

equity_names = {
    "RTY": "Russell 2000 Index",
    "SX5E": "Eurostoxx 50 Index",
    "SD3E": "Eurostoxx Select Dividend 30",
    "SPX": "Standard & Poor 500",
    "TPX": "Tokyo Price Index",
    "IBEX": "IBEX 35",
    "MXEU": "Invesco MSCI Europe UCITS ETF",
    "MXASJ": "MSCI Asia Except Japan Index",
    "MT": "ArcelorMittal SA",
    "EURJPY": "Euro to Japanese Yen exchange rate",
    "EURUSD": "EUR-USD X-RATE",
    "EURBRL": "EUR-BRL X-RATE",
    "GOLD": "Gold Spot",
    "PLDM": "PLDMLNPM Index",
    "LBK": "Liberbank SA",
    "MXESSM": "MXESSM Index",
    "MXITSM": "MXITSM Index",
    "PLTM": "GraniteShares Platinum Trust",
    "SBE": "S&P BRIC 40 EURO Index",
    "NKY": "Nikkei 225",
    "SPGCCLP": "SPGCCLP Index",
    "USDIDR": "USD-IDR X-RATE",
    "USDJPY": "USD-JPY X-RATE",
    "SX7E": "iShares EURO STOXX Banks 30-15 UCITS ETF DE",
    "386 HK Equity": "China Petroleum & Chemical Ord Shs A",
}


class DataFactory:
    """
    Legacy class that reads local Excel files instead of accessing the database through ``beautifulData``.
    """

    def __init__(self, db_object):
        self.db_object = db_object

    def import_discount_curves(
        self,
        *tickers,
        start_date,
        end_date,
        interpolate_missing_dates=True,
        method="bond_spline",
    ):
        """
        Instantiate objects of child classes of DiscountCurve using data of the (Dropbox) DB.

        Parameters
        ----------
        *tickers :  str
            Tickers to be imported. Accepts multiple tickers as separate arguments.
            First date.
        end_date : pandas.DatetimeIndex
            Last date.
        interpolate_missing_dates :  bool, optional
            If ``True`` a linear interpolation is used for having values every day of the year. (default is True)
        method : str, optional
            Specify the method used to interpolate the data of the discount curves (default is "bond_spline").

        Returns
        -------
        dict
            Dictionary with the discount curves (objects of child class of DiscountCurve).

        See Also
        --------
        discount_curves.YieldCurve.fit
            For more details on how the the fit methods are performed.

        """
        curves = {}
        db = self.db_object
        data = db.load_curve(start_date=start_date, end_date=end_date, *tickers)
        # The data is imported from files such as irsw-curves.xlsx, where there is only one date per month (usually at the end of the month).
        # In consequence, if start_date is at the beginning of the month we miss all the dates between start_date and the date for that month in the .xlsx.
        for ticker in data.keys():
            temp_data_dic = data[ticker]
            temp_data = temp_data_dic["Data"]
            specs_temp = temp_data_dic[
                "Specs"
            ]  # We assign a tenor for each curve. This is specified in specs-irsw-curves.xlsx.
            temp_data = temp_data.rename(
                columns={
                    column: specs_temp.loc[column, "Tenor"]
                    for column in temp_data.columns
                }
            )  # We replace the names by the tenors (year fraction).
            calendar_str = temp_data_dic["Curve Specs"].loc[
                "Calendar"
            ]  # For each ticker, the calendar is determined in specs-curves.xlsx
            calendar = self.import_calendar(calendar_str)[calendar_str]
            if interpolate_missing_dates and len(temp_data) != 0:
                temp_data = temp_data.reindex(
                    pd.date_range(start=temp_data.index[0], end=temp_data.index[-1])
                )
                temp_data = temp_data.interpolate(
                    method="linear"
                )  # A linear interpolation for having values every date of the year.
            if temp_data_dic["Curve Specs"].loc["Type"] == "irsw":
                curves[ticker] = CubicSplineSwapCurve(
                    calendar=calendar
                )  # Interest rate Swap
            elif temp_data_dic["Curve Specs"].loc["Type"] == "swi":
                curves[ticker] = DepositCurve(calendar=calendar)  # Swap Index
            if len(temp_data_dic["Data"]) != 0:
                curves[ticker].fit(temp_data, method=method)
            setattr(curves[ticker], "ticker", ticker)
            setattr(curves[ticker], "type", temp_data_dic["Curve Specs"].loc["Type"])
        return curves

    def import_underlying(
        self,
        *tickers,
        start_date="19000101",
        end_date="21000101",
        fillna=True,
        asset_kind=LognormalAsset,
    ):
        """

        Parameters
        ----------
        tickers :  list
            Tickers to be imported.
        start_date : pandas.DatetimeIndex
            First date. By default, ``19000101``
        end_date : pandas.DatetimeIndex
            Last date. By default, ``21000101``
        fillna : bool, default = True
            If True, linear interpolation on asset.data DataFrame when certain values are missing (usually "Volatility" and/or "Dividend Rate").
        asset_kind : data.underlyings.Underlying
            Dynamics followed by the underlying. By default, it is assumed Lognormal dynamics (LognormalAsset).

        Returns
        -------
        dict
            Dictionary with the tickers.
        """
        db = self.db_object
        data = db.load_market_instrument(
            *tickers, start_date=start_date, end_date=end_date
        )
        missing_tickers = [ticker for ticker in tickers if ticker not in data.keys()]
        if len(missing_tickers) != 0:
            print("Missing data for", *missing_tickers)
        dic = {}
        for ticker in data.keys():
            if "Volatility" in data[ticker].columns:
                yieldsdiv = "Dividend Rate" in data[ticker].columns
                asset = asset_kind(
                    ticker=ticker, yieldsdiv=yieldsdiv
                )  # If yieldsdiv == True the corresponing changes are set in underlyings.py.
            else:
                asset = Underlying(ticker=ticker)
            asset.set_data(
                data[ticker]
            )  # The data from the DB is assigned to the asset.
            if fillna:
                asset.fillna()  # Linear interpolation when values are missing (usually "Volatility" and/or "Dividend Rate").
            dic[ticker] = asset
        return dic

    def import_calendar(self, *tickers):
        calendars = {}
        if "ActSecs" in tickers:
            calendars["ActSecs"] = DayCountCalendar(seconds, 365)
        if "Act360" in tickers:
            calendars["Act360"] = DayCountCalendar(actual, 360)
        if "Act365" in tickers:
            calendars["Act365"] = DayCountCalendar(actual, 365)
        if "Cal30360" in tickers:
            calendars["Cal30360"] = MonthYearCalendar(30, 360)

        if "Target2" in tickers:
            initial_year = 2000
            number_years = 100
            years = [initial_year + i for i in range(number_years)]
            target_dates = pd.date_range(
                str(initial_year) + "0101",
                str(initial_year + number_years - 1) + "1231",
            )
            # excluding weekends and fixed holidays
            target_dates = target_dates[target_dates.dayofweek < 5]
            target_dates = target_dates[
                (target_dates.day != 1) + (target_dates.month != 1)
            ]
            target_dates = target_dates[
                (target_dates.day != 1) + (target_dates.month != 5)
            ]
            target_dates = target_dates[
                (target_dates.day != 25) + (target_dates.month != 12)
            ]
            target_dates = target_dates[
                (target_dates.day != 26) + (target_dates.month != 12)
            ]

            def calc_easter(year):
                a = year % 19
                b = year % 4
                c = year % 7
                p = year // 100
                q = (13 + 8 * p) // 25
                m = (15 - q + p - p // 4) % 30
                n = (4 + p - p // 4) % 7
                d = (19 * a + m) % 30
                e = (n + 2 * b + 4 * c + 6 * d) % 7
                days = 22 + d + e
                if (d == 29) and (e == 6):
                    return 4, 19
                elif (d == 28) and (e == 6):
                    return 4, 18
                else:
                    if days > 31:
                        return 4, days - 31
                    else:
                        return 3, days

            for year in years:
                emonth, eday = calc_easter(year)
                if eday == 1:
                    fday = 30
                    fmonth = 3
                elif eday == 2:
                    fday = 31
                    fmonth = 3
                else:
                    fday = eday - 2
                    fmonth = emonth
                target_dates = target_dates[
                    (target_dates.day != fday)
                    + (target_dates.month != fmonth)
                    + (target_dates.year != year)
                ]
                if eday == 31:
                    mday = 1
                    mmonth = 4
                else:
                    mday = eday + 1
                    mmonth = emonth
                target_dates = target_dates[
                    (target_dates.day != mday)
                    + (target_dates.month != mmonth)
                    + (target_dates.year != year)
                ]

            calendars["Target2"] = BusinessCalendar(target_dates, 252)
        return calendars

    def list_discount_curves(self, return_result=False, print_result=True):
        db = self.db_object
        curves = db.list_curves(return_result=return_result, print_result=print_result)
        if return_result:
            return curves

    def list_underlying(self, return_result=False, print_result=True):
        db = self.db_object
        underlyiers = db.list_market_instruments(
            return_result=return_result, print_result=print_result
        )
        if return_result:
            return underlyiers

    def list_calendars(self, return_result=False, print_result=True):
        calendars = ["ActSecs", "Act360", "Act365", "Cal30360", "Target2"]
        if print_result:
            print(*calendars)
        if return_result:
            return calendars


class DataFactoryBeautifulData:
    def __init__(self):
        pass

    @staticmethod
    def list_calendars(return_result=False, print_result=True):
        """
        Return or print the calendars that can be (in principle) imported.

        Parameters
        ----------
        return_result : boolean
            If ``True`` the calendars are returned.
        print_result : boolean
            If ``True`` the calendars are printed.

        Returns
        -------
        list

        Notes
        -----
            Same as the old method :py:meth:`DataFactory.list_calendars<data_factory_bd.DataFactory.list_calendars>`, although now static.
        """
        calendars = ["ActSecs", "Act360", "Act365", "Cal30360", "Target2"]
        if print_result:
            print(*calendars)
        if return_result:
            return calendars

    @staticmethod
    def import_calendar(*tickers):
        """
        Import calendars for day counting.

        Parameters
        ----------
        tickers : list
            Calendars.
        Returns
        -------
        data.calendars.DayCountCalendar

        Notes
        -----
            Same as the old method :py:meth:`DataFactory.import_calendar<data_factory_bd.DataFactory.import_calendar>`, although now static.
        """
        calendars = {}
        if "ActSecs" in tickers:
            calendars["ActSecs"] = DayCountCalendar(seconds, 365)
        if "Act360" in tickers:
            calendars["Act360"] = DayCountCalendar(actual, 360)
        if "Act365" in tickers:
            calendars["Act365"] = DayCountCalendar(actual, 365)
        if "Cal30360" in tickers:
            calendars["Cal30360"] = MonthYearCalendar(30, 360)

        if "Target2" in tickers:
            initial_year = 2000
            number_years = 100
            years = [initial_year + i for i in range(number_years)]
            target_dates = pd.date_range(
                str(initial_year) + "0101",
                str(initial_year + number_years - 1) + "1231",
            )
            # excluding weekends and fixed holidays
            target_dates = target_dates[target_dates.dayofweek < 5]
            target_dates = target_dates[
                (target_dates.day != 1) + (target_dates.month != 1)
            ]
            target_dates = target_dates[
                (target_dates.day != 1) + (target_dates.month != 5)
            ]
            target_dates = target_dates[
                (target_dates.day != 25) + (target_dates.month != 12)
            ]
            target_dates = target_dates[
                (target_dates.day != 26) + (target_dates.month != 12)
            ]

            def calc_easter(year):
                a = year % 19
                b = year % 4
                c = year % 7
                p = year // 100
                q = (13 + 8 * p) // 25
                m = (15 - q + p - p // 4) % 30
                n = (4 + p - p // 4) % 7
                d = (19 * a + m) % 30
                e = (n + 2 * b + 4 * c + 6 * d) % 7
                days = 22 + d + e
                if (d == 29) and (e == 6):
                    return 4, 19
                elif (d == 28) and (e == 6):
                    return 4, 18
                else:
                    if days > 31:
                        return 4, days - 31
                    else:
                        return 3, days

            for year in years:
                emonth, eday = calc_easter(year)
                if eday == 1:
                    fday = 30
                    fmonth = 3
                elif eday == 2:
                    fday = 31
                    fmonth = 3
                else:
                    fday = eday - 2
                    fmonth = emonth
                target_dates = target_dates[
                    (target_dates.day != fday)
                    + (target_dates.month != fmonth)
                    + (target_dates.year != year)
                ]
                if eday == 31:
                    mday = 1
                    mmonth = 4
                else:
                    mday = eday + 1
                    mmonth = emonth
                target_dates = target_dates[
                    (target_dates.day != mday)
                    + (target_dates.month != mmonth)
                    + (target_dates.year != year)
                ]

            calendars["Target2"] = BusinessCalendar(target_dates, 252)
        return calendars

    @staticmethod
    def _read_tenor(
        tenor_index,
    ):  # TODO: We should introduce the calendar/day count for computing the tenors as an argument? For days and weeks.
        """
        Returns the tenor in years of a tenor index of the database.

        Parameters
        ----------
        tenor_index : str
            ``beautifulData`` ticker of the tenor index.

        Returns
        -------
        float
            Tenor in years.

        Notes
        ------
            Tenor Indices are products that refer to different tenors of the same curve.
            For instance the ICE Libor with tenor 6 Months: ``LIBORT6MDX``.

            We will store them as ``r'(?P<root>\w)T(?P<tenor>\d+[DWMY])DX'`` (in python re).
            That is to say:

            root + 'T' + tenor + unit + 'DX'

            where `root` is one or more word characters (which include letters, digits, or underscores),
            `tenor` is one or more digits and the `unit` is one of the letters 'D', 'W', 'M', or 'Y' (day, week, month and year).

            More details in `GitLab link <https://git.arfima.com/arfima/arfima/arfimabox/-/issues/1#note_5499>`_.


        Examples
        --------
        >>> DataFactoryBeautifulData._read_tenor('LIBORT6MDX')
        0.5
        >>> DataFactoryBeautifulData._read_tenor('ROOTT22YDX')
        22
        >>> DataFactoryBeautifulData._read_tenor('Word_1_Word2T48MDX')
        4.0
        """
        pattern = r"(?P<root>\w)T(?P<tenor>\d+[DWMY])DX"  # Pattern for tenor indices in the database.
        match = re.search(pattern, tenor_index)

        if match:
            tenor = match.group("tenor")
        else:
            raise NameError(
                f"{tenor_index} is not a tenor index. An example is LIBORT6MDX."
            )

        # Old version not using python re

        # numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        # units = ['D', 'W', 'M', 'Y']
        # if 'TDX' in tenor_index or not all(char in tenor_index for char in ['T', 'DX'])\
        #         or not any(char in tenor_index for char in units) or not any(char in tenor_index for char in numbers):
        #     raise NameError(f'{tenor_index} is not a tenor index. An example is LIBORT6MDX.')
        #
        # tenor_info = tenor_index
        # while tenor_info[0] not in numbers:  # We need this loop for roots containing the letter 'T'.
        #     tenor_info = tenor_info.split("T", 1)[-1]
        # tenor = tenor_info[:-3]  # We remove the last three characters (unit and 'DX')
        # unit = tenor_info[-3:][0]

        number = int(tenor[:-1])
        unit = tenor[-1]

        if unit == "D":
            return (
                number / 365.0
            )  # days to years   TODO: We should introduce the calendar/day count for computing the tenors here?
        elif unit == "W":
            return (
                number * 7
            ) / 365.0  # weeks to years   TODO: We should introduce the calendar/day count for computing the tenors here?
        elif unit == "M":
            return number / 12.0  # months to years
        else:  # years
            return number

    def _load_curve_bd(self, ticker, start_date, end_date):
        """
        Load one curve from the database using ``beautifulData``.

        Parameters
        ----------
        ticker : string
            Curve to be imported (e.g., 'USD LIBOR').
        start_date : string
            First date.
        end_date : string
            Last date.

        Returns
        -------
        dict
            Dictionary with keys 'Data', 'Specs' and 'Curve Specs'.

        Notes
        -----
            - The idea is to return an object similar to ``BeautifulDataAFSStyleXL.load_curve`` for a single ticker. I.e.,
              ``BeautifulDataAFSStyleXL.load_curve()[ticker]``. The difference here is that ``data_dic['Specs']`` is not included since
              we already include the numeric tenor as the name of the column (by using the method :py:meth:`self._read_tenor <data_factory_bd.DataFactoryBeautifulData._read_tenor>`).
            - We always assume End Of Day (eod) data.
        """
        data_dic = {}
        instruments_bd = list(
            specs.discount_curves[ticker][-1]
        )  # List with the instruments of bd (one ticker for each tenor).
        load_dict = bd.load(
            tickers=instruments_bd,
            dtype="eod",
            from_date=start_date,
            to_date=end_date,
        )  # Note that the returned values are "Decimals".
        if len(load_dict.keys()) != len(instruments_bd):
            raise NameError("Not all the instruments have been imported.")
        # List with the DataFrames for each tenor. We go from Decimals to floats.
        list_df = [
            # TODO: df.index = pd.to_datetime(df.index)  # From Index to DatetimeIndex?
            (
                load_dict[instr]
                .df.drop(columns="instrument", errors="ignore")
                .applymap(float)
                / 100
            ).rename(columns={"close": self._read_tenor(instr)})
            for i, instr in enumerate(load_dict.keys())
        ]  # We change the name of the columns and divide by 100, so we got the same format as before (db_tools).
        for df in list_df:
            df.index = pd.to_datetime(df.index)  # From Index to DatetimeIndex
            df = df.dropna()  # We remove the ``Nones`` due to holidays.
        common_dates = pd.to_datetime(list_df[0].index)
        for df in list_df[1:]:
            common_dates = common_dates.intersection(
                df.index
            )  # Each DataFrame to have the same index
        list_df = [df.loc[common_dates] for df in list_df]
        data_dic["Data"] = pd.concat(list_df, axis=1)
        # data_dic['Specs'] = pd.DataFrame({'Tenor': eval(ticker2)})  # Not needed since we already include the numeric tenor as the name of the column.
        data_dic["Curve Specs"] = pd.Series(
            [specs.discount_curves[ticker][0], specs.discount_curves[ticker][1]],
            index=["Type", "Calendar"],
        )
        return data_dic

    @staticmethod
    def list_discount_curves(fields=True):
        """
        Return discount curves that can be imported.

        Parameters
        ----------
        fields : bool, optional
             If ``True`` the details of the curve are also shown. The default is ``True``.

        Notes
        -------
            When fields is ``True``, this method prints a dict of tuples with the following format for each discount curve (key):

            - Discount curve name : {'kind of curve' (str), 'Day Count' (str), 'Tickers' (tuple)}
            - In this case 'Tickers' is a tuple of strings with the tickers from ``beautifulData`` used for constructing the curve.
        """
        if fields:
            print(specs.discount_curves)
        else:
            print(list(specs.discount_curves.keys()))

    def import_discount_curves(self, *tickers, start_date, end_date):
        """
        Instantiate objects of child classes of :py:meth:`DiscountCurve <pricing.discount_curves.DiscountCurve>` using ``beautifulData``.

        Parameters
        ----------
        *tickers :  str
            Tickers to be imported. Accepts multiple tickers as separate arguments.
            Use DataFactoryBeautifulData.list_discount_curves() to see the list of tickers that can be imported.
        start_date : string
            First date.
        end_date : string
            Last date.

        Returns
        -------
        dict
            Dictionary with the discount curves (objects of child class of :py:meth:`DiscountCurve <pricing.discount_curves.DiscountCurve>`).
        Examples
        -------
        >>> factory_bd = DataFactoryBeautifulData()
        dict_disc_curves = factory_bd.import_discount_curves("USD LIBOR", start_date="20220101", end_date="20220301")
        """
        # TODO: ADD >>> to docstring once the database is filled (now raises RecursionError).
        curves = {}
        data = {
            ticker: self._load_curve_bd(
                ticker, start_date=start_date, end_date=end_date
            )
            for ticker in tickers
        }
        # Now we have the same as in the old method (DataFactory.import_discount_curves(...), so we just simply use it.
        for ticker in data.keys():
            temp_data_dic = data[ticker]
            temp_data = temp_data_dic["Data"]
            # This is not needed now since the columns are the numeric tenors from self.__load_curve_bd
            # specs = temp_data_dic["Specs"]  # We assign a tenor for each curve. This is specified in specs-irsw-curves.xlsx.
            # temp_data = temp_data.rename(columns={column: specs.loc[column, "Tenor"] for column in temp_data.columns})  # We replace the names by the tenors (year fraction).
            calendar_str = temp_data_dic["Curve Specs"].loc[
                "Calendar"
            ]  # For each ticker, the calendar is determined in specs-curves.xlsx
            calendar = self.import_calendar(calendar_str)[calendar_str]
            if len(temp_data) != 0:
                temp_data = temp_data.reindex(
                    pd.date_range(
                        start=temp_data.index[0], end=temp_data.index[-1]
                    )  # We include holidays (specially weekends)
                )
                temp_data = temp_data.interpolate(
                    method="linear"
                )  # We use a linear interpolation for having data on holidays.
                # TODO: Maybe we don't need to have data on holidays since the discount D(t, T) is not going to be used (in principle) when t is a holiday.
            if (
                temp_data_dic["Curve Specs"].loc["Type"] == "irsw"
            ):  # TODO: Makes sense? The distinction 'irsw' and 'swi'. See [Hull].
                curves[ticker] = CubicSplineSwapCurve(
                    calendar=calendar
                )  # Interest rate Swap
            elif temp_data_dic["Curve Specs"].loc["Type"] == "swi":
                curves[ticker] = DepositCurve(calendar=calendar)  # Swap Index
            if len(temp_data_dic["Data"]) != 0:
                curves[ticker].fit(temp_data)
            setattr(curves[ticker], "ticker", ticker)
            setattr(curves[ticker], "type", temp_data_dic["Curve Specs"].loc["Type"])
        return curves

    @staticmethod
    def _load_underlying_bd(
        ticker, start_date, end_date, volatility_kind, dividend_kind
    ):
        """
        Load one underlying from the database using ``beautifulData``.

        Parameters
        ----------
        ticker : string
            Underlying to be imported. We should use the ``beautifulData`` ticker for the instrument (not for the product). For example, ``SPX`` is the product and
            ``SPXIDX`` the instrument.
        start_date : str
            First date.
        end_date : str
            Last date.

        Returns
        -------
        pandas.Dataframe
            DataFrame with dates as the index and relevant fields as columns. In general, these will be ``{'Price', 'Volatility', 'Dividend Rate'}``.

        Notes
        -----
            - The idea is to return the same object as ``BeautifulDataAFSStyleXL.load_market_instrument`` for a single ticker. I.e.,
              ``BeautifulDataAFSStyleXL.load_market_instrument()[ticker]``.
            - We always assume End Of Day (eod) data.
        """
        data_dic = {}
        load_dict = bd.load(
            tickers=ticker,
            dtype="eod",
            from_date=start_date,
            to_date=end_date,
        )  # Note that the returned values are "Decimals".
        # Instead of a LoadDict we want the DataFrame
        df_str = "load_dict." + ticker + "_eod.df"  # beautifulData conventions
        df = eval(df_str)
        # df = df.dropna()  # We remove the ``Nones`` due to holidays.
        df = df.drop(columns="instrument", errors="ignore")
        df = df.map(float, na_action="ignore")  # From Decimals to floats.
        df.index = pd.to_datetime(df.index)  # From Index to DatetimeIndex
        columns_to_keep = []
        # We change the name of the columns (we use the ones in the old DataFactory)
        if "close" not in df.columns:
            print(
                f"{ticker} does not have the field: close."
            )  # TODO: Use warnings (warnings.warn) instead of prints.
        else:
            df = df.rename(columns={"close": "Price"})
            columns_to_keep.append("Price")
        if volatility_kind not in df.columns:
            print(f"{ticker} does not have the field: {volatility_kind}.")
        else:
            df["Volatility"] = (
                df.pop(volatility_kind) / 100
            )  # We divide by 100, volatility per unit (100 bp = 0.01 per unit)
            columns_to_keep.append("Volatility")
        if dividend_kind not in df.columns:
            print(f"{ticker} does not have the field: {dividend_kind}.")
        else:
            df["Dividend Rate"] = (
                df.pop(dividend_kind) / 100
            )  # We divide by 100, dividend rates per unit (100 bp = 0.01 per unit)
            columns_to_keep.append("Dividend Rate")
        df = df[columns_to_keep]  # We remove unused columns
        return df

    @staticmethod
    def list_underlyings(fields=True):
        """
        Return the underyings that can be imported.

        Parameters
        ----------
        fields : boolean, optional
             If ``True`` the volatilities and dividends available for each ticker are also shown. The default is ``True``.

        """
        if fields:
            list_instruments = [
                product + "IDX" for product in specs.underlying_products
            ]
            load_dict = bd.load(
                tickers=list_instruments,
                dtype="eod",
                from_date="20220118",  # We only import two (business) days (we don't really need the data, just the fields)
                to_date="20220119",  # The days chosen are arbitrary. Note that this is not optimal.
            )
            list_instruments_eod = [
                instrument + "_eod" for instrument in list_instruments
            ]  # beautifulData conventions
            dict = {}
            for i in range(len(list_instruments)):
                list_temp = afsfun.contains_word(
                    load_dict[list_instruments_eod[i]].columns, "volatility"
                )
                list_temp.append(
                    afsfun.contains_word(
                        load_dict[list_instruments_eod[i]].columns, "dividend"
                    )
                )
                dict[list_instruments[i]] = list_temp
            print(dict)
        else:
            print(specs.underlying_products)
            print(
                "Note that the ticker for the instrument follows the rule 'product' + 'IDX'."
            )

    def import_underlying(
        self,
        *tickers,
        start_date="19000101",
        end_date="21000101",
        fillna=True,
        asset_kind=LognormalAsset,
        volatility_kind="realized_volatility_30d",
        dividend_kind="forward_dividend_yield",
    ):
        """
        Import the underlyings specified by tickers.

        Parameters
        ----------
        *tickers :  str
            Tickers to be imported. Accepts multiple tickers as separate arguments.
            Use :py:meth:`list_underlyings<data_factory_bd.DataFactoryBeautifulData.list_underlyings>` to see the list of tickers that can be imported.
        start_date : str
            First date.
        end_date : str
            Last date.
        asset_kind : data.underlyings.Underlying
            Dynamics followed by the underlying. By default, it is assumed Lognormal dynamics (``LognormalAsset``).
        volatility_kind : str
            Kind of volatility needed. The ``beautifulData`` name (see Mimir) should be used. This method uses the same volatility for every ticker.
        dividend_kind : str
            Kind of dividend needed. The ``beautifulData`` name (see Mimir) should be used. This method uses the same dividend for every ticker.

        Returns
        -------
        dict
            Dictionary with the tickers.

        Examples
        -------
        >>> factory_bd = DataFactoryBeautifulData()
        >>> dict_und = factory_bd.import_underlying("SPXIDX", "SX5EIDX", start_date="20220101", end_date="20220301")
        """
        if not (asset_kind in tuple(specs.underlying_dynamics_classes)):
            raise ValueError(
                f"Underlying dynamics not supported. Try with {specs.underlying_dynamics}"
            )
        else:
            data = {
                ticker: self._load_underlying_bd(
                    ticker, start_date, end_date, volatility_kind, dividend_kind
                )
                for ticker in tickers
            }
            missing_tickers = [
                ticker for ticker in tickers if ticker not in data.keys()
            ]
            if len(missing_tickers) != 0:
                print("Missing data for", *missing_tickers)
            dic = {}
            for ticker in data.keys():
                if "Volatility" in data[ticker].columns:
                    yieldsdiv = "Dividend Rate" in data[ticker].columns
                    asset = asset_kind(
                        ticker=ticker, yieldsdiv=yieldsdiv
                    )  # If yieldsdiv == True the corresponing changes are set in underlyings.py.
                else:
                    asset = Underlying(ticker=ticker)
                asset.set_data(
                    data[ticker]
                )  # The data from the DB is assigned to the asset.
                if fillna:
                    asset.fillna()  # Linear interpolation when values are missing (usually "Volatility" and/or "Dividend Rate")
                dic[ticker] = asset
            return dic

    def import_volatility_smile(
        ticker,
        maturity,
        from_date,
        to_date,
        strike_min=None,
        strike_max=None,
        call_put="C",
        fit=True,
    ):
        """
        Create ``VolatilitySmile`` objects for a range of dates, :math:`t \\in [t_0, t_1]`,
        and specified parameters.

        Parameters
        ----------
        ticker : str
            The underlying asset's ticker symbol.
        maturity : date
            The option's maturity, :math:`T`.
        from_date : str
            The start date for retrieving option data, :math:`t_0`.
        to_date : str
            The end date for retrieving option data, :math:`t_1`.
        strike_min : float, optional
            Minimum strike price filter. Default is None.
        strike_max : float, optional
            Maximum strike price filter. Default is None.
        call_put : str, optional
            Option type, "C" for call options (default) or "P" for put options.
        fit : bool, optional
            If True, fit a volatility smile to the data. Default is True.

        Returns
        -------
        dict_smiles : dict or pricing.implied_volatility.VolatilitySmile
            A dictionary of ``VolatilitySmile``  objects, where keys are dates and values are
            instances of the ``VolatilitySmile`` class. If there is only one value, it returns
            the only value.

        Notes
        -----
        This function retrieves option data for a range of dates within the specified date range
        and with optional filters on strike prices. It creates ``VolatilitySmile`` objects for each
        date and returns them in a dictionary. The ``VolatilitySmile``  objects can be used to analyze
        and visualize the volatility smiles for the options on different dates.

        Examples
        --------
        >>> ticker = "SX5EIDX"
        >>> maturity = "2023-09-15"
        >>> from_date = "2023-06-08"
        >>> to_date ="2023-06-15"
        >>> smile_dict = afs.DataFactoryBeautifulData.import_volatility_smile(ticker, maturity, from_date=from_date, to_date=to_date, call_put="P")

        """
        data = bd.load_option(
            underlying_tickers=ticker,
            from_date=from_date,
            to_date=to_date,
            call_put=call_put,
            strike_min=strike_min,
            strike_max=strike_max,
            maturity_max=maturity,
            maturity_min=maturity,
            name_df=ticker,
        )
        underlyings = bd.load(
            tickers=ticker, from_date=from_date, to_date=to_date, dtype="eod"
        )
        underlyings = underlyings[ticker + "_eod"].df
        df = data[ticker].df
        grouped = df.groupby("dtime")
        dict_smiles = {}
        for name, group in grouped:
            df = group.sort_values(by="strike", ascending=True)
            spot = underlyings["close"].loc[name]
            if spot is not None:
                spot = float(spot)
            smile = VolatilitySmile(
                dtime=name,
                maturity=maturity,
                underlying_ticker=ticker,
                spot=spot,
                strikes=df["strike"].astype(float),
                implied_vols=df["stock"],
                direction=call_put,
            )

            if fit:
                smile.fit()
            dict_smiles[name] = smile

        if from_date == to_date:
            return dict_smiles[name]
        else:
            return dict_smiles

    def import_volatility_surface(
        ticker,
        date,
        calendar,
        strike_min=None,
        strike_max=None,
        maturity_min=None,
        maturity_max=None,
        call_put="C",
        fit=True,
        delta=False,
        enable_pbar=True,
    ):
        """
        Create a ``VolatilitySurface`` object for a specific date and specified parameters.

        Parameters
        ----------
        ticker : str
            The underlying asset's ticker symbol.
        date : str
            The date for retrieving option data, :math:`t`.
        calendar : data.calendars.DayCountCalendar
                The calendar system (Day Count Convention) to use when computing intervals.
                Calendar should be understood as an element of the classes defined in calendar.py.
        strike_min : float, optional
            Minimum strike price filter. Default is None.
        strike_max : float, optional
            Maximum strike price filter. Default is None.
        maturity_min : date, optional
            Minimum maturity date filter. Default is None.
        maturity_max : date, optional
            Maximum maturity date filter. Default is None.
        call_put : str, optional
            Option type, "C" for call options (default) or "P" for put options.
        fit : bool, optional
            If True, fit a volatility surface to the data. Default is True.
        delta : bool, optional
            If True, returns an instance of ``VolatilitySurfaceDelta``. Default is False.
        enable_pbar : bool, optional
            If True, display the loading data bar. Default is True.

        Return
        ------
        VolatilitySurface : pricing.implied_volatility.VolatilitySurface orpricing.implied_volatility.VolatilitySurfaceDelta

        Notes
        -----
        This function retrieves option data for a specific date, :math:`t`, with optional filters on strike
        prices, :math:`K`, and maturity dates, :math:`T`, using BeautifulData. It creates a ``VolatilitySurface`` object
        for the specified date and returns it. The ``VolatilitySurface`` object can be used to
        analyze and visualize the volatility surface for the options on that date.

        Examples
        --------
        >>> ticker = "SX5EIDX"
        >>> date = "2023-06-07"
        >>> surface = afs.DataFactoryBeautifulData.import_volatility_surface(ticker, date, strike_max=4600, strike_min=3800, calendar=calendars["Act365"], call_put="C")
        >>> surface.fit(verbose=True)
        >>> surface.plot_strike()
        """
        data = bd.load_option(
            underlying_tickers=ticker,
            from_date=date,
            to_date=date,
            call_put=call_put,
            strike_min=strike_min,
            strike_max=strike_max,
            maturity_max=maturity_max,
            maturity_min=maturity_min,
            name_df=ticker,
            enable_pbar=enable_pbar,
        )
        df = data[ticker].df
        df = df.dropna(subset=["stock"])
        df = df.sort_values(by="strike", ascending=True)
        underlying = bd.load(
            tickers=ticker,
            to_date=date,
            from_date=date,
            dtype="eod",
            enable_pbar=enable_pbar,
        )
        underlying = underlying[ticker + "_eod"].df

        if delta:
            surface = VolatilitySurfaceDelta(
                dtime=date,
                maturities=df["maturity"],
                underlying_ticker=ticker,
                spot=float(underlying["close"][0]),
                strikes=df["strike"].astype(float),
                implied_vols=df["stock"],
                direction=call_put,
                calendar=calendar,
            )

        else:
            surface = VolatilitySurface(
                dtime=date,
                maturities=df["maturity"],
                underlying_ticker=ticker,
                spot=float(underlying["close"][0]),
                strikes=df["strike"].astype(float),
                implied_vols=df["stock"],
                direction=call_put,
                calendar=calendar,
            )

            if fit:
                surface.fit()

        return surface


if __name__ == "__main__":
    # Code block to be executed when the script is run directly
    print(bd.__version__)
