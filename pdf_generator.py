# Written by: Wren J. Rudolph
from __future__ import print_function
from __future__ import print_function

from ConfigParser import ConfigParser

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, inch, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus import Spacer

from line_chart_generator import LineChartGenerator

config = ConfigParser()
config.read('config.ini')


class PdfGenerator(object):
    def __init__(self,
                 weekly_standings_results,
                 weekly_score_results,
                 weekly_coaching_efficiency_results,
                 weekly_luck_results,
                 num_tied_scores,
                 num_tied_efficiencies,
                 num_tied_luck,
                 efficiency_dq_count,
                 league_id,
                 report_title_text,
                 report_footer_text,
                 standings_title_text,
                 points_title_text,
                 tied_weekly_score_bool,
                 coaching_efficiency_title_text,
                 tied_weekly_coaching_efficiency_bool,
                 luck_title_text,
                 tied_weekly_luck_bool,
                 weekly_team_points_by_position):

        self.weekly_standings_results = weekly_standings_results
        self.weekly_score_results = weekly_score_results
        self.weekly_coaching_efficiency_results = weekly_coaching_efficiency_results
        self.weekly_luck_results = weekly_luck_results
        self.num_tied_scores = num_tied_scores
        self.num_tied_efficiencies = num_tied_efficiencies
        self.num_tied_luck = num_tied_luck
        self.efficiency_dq_count = efficiency_dq_count
        self.league_id = league_id
        self.report_footer_text = report_footer_text
        self.tied_points_bool = tied_weekly_score_bool
        self.tied_efficiency_bool = tied_weekly_coaching_efficiency_bool
        self.tied_luck_bool = tied_weekly_luck_bool
        self.weekly_team_points_by_position = weekly_team_points_by_position

        # Configure style and word wrap
        self.stylesheet = getSampleStyleSheet()
        self.text_style = self.stylesheet["BodyText"]
        self.text_styleN = self.stylesheet['Normal']
        self.text_styleH = self.stylesheet['Heading3']
        self.text_styleT = self.stylesheet['Heading2']
        self.text_style.wordWrap = 'CJK'

        title_table_style_list = [
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ]

        self.title_style = TableStyle(title_table_style_list)

        # Reportlab fonts: https://github.com/mattjmorrison/ReportLab/blob/master/src/reportlab/lib/fonts.py
        table_style_list = [
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.green),
            ('FONT', (0, 1), (-1, 1), 'Helvetica-Oblique'),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('GRID', (0, 0), (-1, 0), 1.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
        ]

        self.style = TableStyle(table_style_list)

        self.num_tied_scores = num_tied_scores
        tied_scores_iterator = num_tied_scores + 1
        tied_scores_table_style_list = list(table_style_list)

        if league_id == config.get("Fantasy_Football_Report_Settings", "league_of_emperors_id"):
            tied_scores_table_style_list.append(('TEXTCOLOR', (0, 1), (-1, 1), colors.green))
            tied_scores_table_style_list.append(('FONT', (0, 1), (-1, 1), 'Helvetica-Oblique'))
        else:
            index = 1
            while tied_scores_iterator > 0:
                tied_scores_table_style_list.append(('TEXTCOLOR', (0, index), (-1, index), colors.green))
                tied_scores_table_style_list.append(('FONT', (0, index), (-1, index), 'Helvetica-Oblique'))
                tied_scores_iterator -= 1
                index += 1

        tied_efficiencies_iterator = num_tied_efficiencies + 1
        tied_efficiencies_table_style_list = list(table_style_list)
        index = 1
        while tied_efficiencies_iterator > 0:
            tied_efficiencies_table_style_list.append(('TEXTCOLOR', (0, index), (3, index), colors.green))
            tied_efficiencies_table_style_list.append(('FONT', (0, index), (3, index), 'Helvetica-Oblique'))
            tied_efficiencies_iterator -= 1
            index += 1

        tied_luck_iterator = num_tied_luck + 1
        tied_luck_table_style_list = list(table_style_list)
        index = 1
        while tied_luck_iterator > 0:
            tied_luck_table_style_list.append(('TEXTCOLOR', (0, index), (3, index), colors.green))
            tied_luck_table_style_list.append(('FONT', (0, index), (3, index), 'Helvetica-Oblique'))
            tied_luck_iterator -= 1
            index += 1

        self.style_tied_scores = TableStyle(tied_scores_table_style_list)
        self.style_tied_efficiencies = TableStyle(tied_efficiencies_table_style_list)
        self.style_tied_luck = TableStyle(tied_luck_table_style_list)

        dq_index = len(weekly_score_results) - efficiency_dq_count + 1

        if num_tied_efficiencies > 0:
            efficiencies_dq_table_style_list = list(tied_efficiencies_table_style_list)
        else:
            efficiencies_dq_table_style_list = list(table_style_list)

        if efficiency_dq_count > 0:

            while efficiency_dq_count > 0:
                efficiencies_dq_table_style_list.append(('TEXTCOLOR', (0, dq_index), (3, dq_index), colors.red))
                efficiency_dq_count -= 1
                dq_index += 1

        self.style_efficiency_dqs = TableStyle(efficiencies_dq_table_style_list)

        # options: "document", "section", or None/empty
        self.report_title = self.create_title(report_title_text, element_type="document")
        self.standings_title = self.create_title(standings_title_text, element_type="section")
        self.points_title = self.create_title(points_title_text, element_type="section")
        self.efficiency_title = self.create_title(coaching_efficiency_title_text, element_type="section")
        self.luck_title = self.create_title(luck_title_text, element_type="section")

    def create_title(self, title_text, element_type=None):

        if element_type == "document":
            title_text_style = self.text_styleT
        elif element_type == "section":
            title_text_style = self.text_styleH
        else:
            title_text_style = self.text_styleN

        title = Paragraph('''<para align=center spaceb=3><b>''' + title_text + '''</b></para>''', title_text_style)
        title_table = Table([[title]], colWidths=[5 * inch] * 1)
        title_table.setStyle(self.title_style)
        return title_table

    def create_data_table(self, col_headers, data, table_style_for_ties, col_widths=None, tied_metric_bool=False):

        [col_headers.append(item) for item in data]
        table = Table(col_headers, colWidths=col_widths)

        if tied_metric_bool:
            table.setStyle(table_style_for_ties)
        else:
            table.setStyle(self.style)
        return table

    @staticmethod
    def create_line_chart(data, data_length, series_names, chart_title, x_axis_title, y_axis_title, y_step):

        series_colors = [
            [100, 0, 0, 0, 100],
            [100, 50, 0, 0, 100],
            [100, 100, 0, 0, 100],
            [50, 100, 0, 0, 100],
            [0, 100, 0, 0, 100],
            [0, 100, 50, 0, 100],
            [0, 100, 100, 0, 100],
            [0, 50, 100, 0, 100],
            [0, 0, 100, 0, 100],
            [50, 0, 100, 0, 100],
            [100, 0, 100, 0, 100],
            [100, 0, 50, 0, 100]
        ]

        box_width = 550
        box_height = 240
        chart_width = 490
        chart_height = 150

        # fit y-axis of table
        values = [weeks[1] for teams in data for weeks in teams]
        values_min = min(values)
        values_max = max(values)

        points_line_chart = LineChartGenerator(series_colors, box_width, box_height, chart_width, chart_height)
        points_line_chart.make_title(chart_title)
        points_line_chart.make_data(data)
        points_line_chart.make_x_axis(x_axis_title, 0, data_length + 1, 1)
        points_line_chart.make_y_axis(y_axis_title, values_min, values_max, y_step)
        points_line_chart.make_series_labels(series_names)

        return points_line_chart

    def generate_pdf(self, filename_with_path, chart_data_list):

        elements = []
        spacer_small = Spacer(1, 0.05 * inch)
        spacer_large = Spacer(1, 0.10 * inch)
        metric_scores_col_widths = [0.75 * inch, 1.75 * inch, 1.75 * inch, 2.00 * inch]

        doc = SimpleDocTemplate(filename_with_path, pagesize=LETTER, rightMargin=25, leftMargin=25, topMargin=10,
                                bottomMargin=10)
        doc.pagesize = portrait(LETTER)

        elements.append(self.report_title)
        elements.append(spacer_large)

        elements.append(self.standings_title)
        standings_headers = [
            ["Place", "Team", "Manager", "Record", "Points For", "Points Against", "Streak", "Waiver", "Moves",
             "Trades"]]
        standings_col_widths = [0.50 * inch, 1.75 * inch, 1.00 * inch, 1.00 * inch, 0.80 * inch, 1.10 * inch,
                                0.50 * inch, 0.50 * inch, 0.50 * inch, 0.50 * inch]
        elements.append(
            self.create_data_table(standings_headers, self.weekly_standings_results, self.style, standings_col_widths))

        elements.append(PageBreak())
        elements.append(self.points_title)
        points_headers = [["Place", "Team", "Manager", "Points"]]
        if self.num_tied_scores > 0:
            if self.league_id == config.get("Fantasy_Football_Report_Settings", "league_of_emperors_id"):
                points_headers[0].append("Bench Points")
            else:
                for index, team in enumerate(self.weekly_score_results):
                    self.weekly_score_results[index] = team[:-1]
        else:
            for index, team in enumerate(self.weekly_score_results):
                self.weekly_score_results[index] = team[:-1]

        elements.append(self.create_data_table(points_headers, self.weekly_score_results, self.style_tied_scores,
                                               metric_scores_col_widths, self.tied_points_bool))

        if self.tied_points_bool:
            if self.league_id != config.get("Fantasy_Football_Report_Settings", "league_of_emperors_id"):
                elements.append(Paragraph(
                    "<i>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*Tie for first place.</i>",
                    getSampleStyleSheet()["Normal"]))

        elements.append(spacer_small)
        elements.append(self.efficiency_title)
        efficiency_headers = [["Place", "Team", "Manager", "Coaching Efficiency (%)"]]
        coaching_efficiency_table = self.create_data_table(efficiency_headers, self.weekly_coaching_efficiency_results,
                                                           self.style_tied_efficiencies, metric_scores_col_widths,
                                                           self.tied_efficiency_bool)
        if self.efficiency_dq_count > 0:
            coaching_efficiency_table.setStyle(self.style_efficiency_dqs)
        elements.append(coaching_efficiency_table)

        if self.tied_efficiency_bool:
            elements.append(spacer_small)
            if self.league_id == config.get("Fantasy_Football_Report_Settings", "league_of_emperors_id"):
                elements.append(Paragraph(
                    "<i>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*The league commissioner will resolve coaching efficiency ties manually. The winner will be the manager whose team contains the most players who have exceeded their average weekly fantasy points.</i>",
                    getSampleStyleSheet()["Normal"]))
            else:
                elements.append(Paragraph(
                    "<i>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*Tie for first place.</i>",
                    getSampleStyleSheet()["Normal"]))

        elements.append(spacer_small)
        elements.append(self.luck_title)
        luck_headers = [["Place", "Team", "Manager", "Luck (%)"]]
        elements.append(self.create_data_table(luck_headers, self.weekly_luck_results, self.style_tied_luck,
                                               metric_scores_col_widths, self.tied_luck_bool))

        if self.tied_luck_bool:
            elements.append(Paragraph(
                "<i>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*Tie for first place.</i>",
                getSampleStyleSheet()["Normal"]))

        elements.append(PageBreak())

        series_names = chart_data_list[0]
        managers = chart_data_list[1]
        points_data = chart_data_list[2]
        efficiency_data = chart_data_list[3]
        luck_data = chart_data_list[4]

        # calculate season averages for points, coaching efficiency, and luck
        season_average_points = []
        season_average_coaching_efficiency = []
        season_average_luck = []
        team_index = 0
        for team in series_names:
            team_points_average = sum([float(i[1]) for i in points_data[team_index]]) / float(
                len(points_data[team_index]))
            season_average_points.append([team, managers[team_index], team_points_average])
            team_efficiency_average = sum([float(i[1]) for i in efficiency_data[team_index]]) / float(
                len(efficiency_data[team_index]))
            season_average_coaching_efficiency.append([team, managers[team_index], team_efficiency_average])
            team_luck_average = sum([float(i[1]) for i in luck_data[team_index]]) / float(len(luck_data[team_index]))
            season_average_luck.append([team, managers[team_index], team_luck_average])
            team_index += 1

        ordered_average_points = sorted(season_average_points, key=lambda x: float(x[2]), reverse=True)
        average_points_data = []
        place = 1
        for team in ordered_average_points:
            average_points_data.append([place, team[0], team[1], "{0:.2f}".format(team[2])])
            place += 1

        ordered_average_efficiency = sorted(season_average_coaching_efficiency, key=lambda x: float(x[2]), reverse=True)
        average_efficiency_data = []
        place = 1
        for team in ordered_average_efficiency:
            average_efficiency_data.append([place, team[0], team[1], "{0:.2f}%".format(team[2])])
            place += 1

        ordered_average_luck = sorted(season_average_luck, key=lambda x: float(x[2]), reverse=True)
        average_luck_data = []
        place = 1
        for team in ordered_average_luck:
            average_luck_data.append([place, team[0], team[1], "{0:.2f}%".format(team[2])])
            place += 1

        # create season average tables for points, coaching efficiency, and luck
        elements.append(self.create_title("Season Average Points", element_type="section"))
        points_headers = [["Place", "Team", "Manager", "Points"]]
        elements.append(self.create_data_table(points_headers, average_points_data, self.style,
                                               col_widths=metric_scores_col_widths))
        elements.append(spacer_small)
        elements.append(self.create_title("Season Average Coaching Efficiency", element_type="section"))
        efficiency_headers = [["Place", "Team", "Manager", "Coaching Efficiency (%)"]]
        elements.append(self.create_data_table(efficiency_headers, average_efficiency_data, self.style,
                                               col_widths=metric_scores_col_widths))
        elements.append(spacer_small)
        elements.append(self.create_title("Season Average Luck", element_type="section"))
        luck_headers = [["Place", "Team", "Manager", "Luck (%)"]]
        elements.append(
            self.create_data_table(luck_headers, average_luck_data, self.style, col_widths=metric_scores_col_widths))
        elements.append(PageBreak())

        # Remove any zeros from coaching efficiency to make table prettier
        for team in efficiency_data:
            week_index = 0
            for week in team:
                if week[1] == 0.0:
                    del team[week_index]
                week_index += 1

        # create line charts for points, coaching efficiency, and luck
        elements.append(self.create_line_chart(points_data, len(points_data[0]), series_names, "Weekly Points", "Weeks",
                                               "Fantasy Points", 10.00))
        elements.append(spacer_small)
        elements.append(
            self.create_line_chart(efficiency_data, len(points_data[0]), series_names, "Weekly Coaching Efficiency",
                                   "Weeks", "Coaching Efficiency (%)", 5.00))
        elements.append(spacer_small)
        elements.append(
            self.create_line_chart(luck_data, len(points_data[0]), series_names, "Weekly Luck", "Weeks", "Luck (%)",
                                   20.00))
        elements.append(spacer_large)
        elements.append(Paragraph(self.report_footer_text, getSampleStyleSheet()["Normal"]))

        print("generating pdf...\n")
        doc.build(elements)
        print("... pdf generated!\n")

        return doc.filename
