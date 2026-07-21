import panel as pn
import hvplot.pandas
import pandas as pd
import numpy as np
import param

pn.extension()


# ── Load data ──────────────────────────────────────────────
wildfire_agg = pd.read_csv('data/wildfire_agg.csv')
wildfire_sample = pd.read_csv('data/wildfire_sample.csv')

# ── Shared color mapping ───────────────────────────────────
cause_colors = {
    'Human': '#f1ce63',
    'Natural': '#4e79a7',
    'Undetermined': '#e15759',
}

CHART_WIDTH = 560
CHART_HEIGHT = 380


class WildfireDashboard(param.Parameterized):
    year_range = param.Range(default=(1992, 2020), bounds=(1992, 2020))
    cause_groups = param.ListSelector(
        default=['Human', 'Natural', 'Undetermined'],
        objects=['Human', 'Natural', 'Undetermined']
    )

    @param.depends('cause_groups')
    def line_chart(self):
        selected = self.cause_groups if self.cause_groups else ['Human', 'Natural', 'Undetermined']
        data = wildfire_agg[wildfire_agg['CAUSE'].isin(selected)]
        data = data.groupby(['FIRE_YEAR', 'CAUSE'])['fire_count'].sum().reset_index()
        return data.hvplot.line(
            x='FIRE_YEAR', y='fire_count', by='CAUSE',
            color=[cause_colors[c] for c in selected],
            width=CHART_WIDTH, height=CHART_HEIGHT,
            xlabel='Year', ylabel='Number of Fires',
            title='Wildfires per Year by Cause Category',
            ylim=(0, 100000), yformatter='%.0f',
            hover_cols=['FIRE_YEAR', 'fire_count', 'CAUSE']
        ).opts(
            tools=['hover'],
            hover_tooltips=[('Year', '@FIRE_YEAR'), ('Fires', '@fire_count{0,0}'), ('Category', '@CAUSE')]
        )

    @param.depends()
    def bar_chart(self):
        totals = wildfire_agg.groupby('CAUSE')['total_acres'].sum().reset_index().sort_values(
            'total_acres', ascending=False
        )
        return totals.hvplot.bar(
            x='CAUSE', y='total_acres',
            color='CAUSE', cmap=cause_colors,
            width=CHART_WIDTH, height=CHART_HEIGHT,
            xlabel='Cause Category', ylabel='Total Acres Burned',
            title='Total Acres Burned by Cause Category (1992–2020)',
            yformatter='%.0f', legend=False,
            hover_cols=['CAUSE', 'total_acres']
        ).opts(
            tools=['hover'],
            hover_tooltips=[('Category', '@CAUSE'), ('Total Acres', '@total_acres{0,0}')]
        )

    @param.depends('year_range', 'cause_groups')
    def scatter_chart(self):
        selected = self.cause_groups if self.cause_groups else ['Human', 'Natural', 'Undetermined']
        data = wildfire_sample[
            (wildfire_sample['FIRE_YEAR'] >= self.year_range[0]) &
            (wildfire_sample['FIRE_YEAR'] <= self.year_range[1]) &
            (wildfire_sample['CAUSE'].isin(selected))
        ]
        data = data.dropna(subset=['DAYS_TO_CONTAIN'])
        data = data[data['DAYS_TO_CONTAIN'] >= 0]
        return data.hvplot.scatter(
            x='DAYS_TO_CONTAIN', y='FIRE_SIZE',
            by='CAUSE',
            color=[cause_colors[c] for c in selected],
            logy=True, alpha=0.35, size=25,
            width=CHART_WIDTH, height=CHART_HEIGHT,
            xlabel='Days to Containment', ylabel='Fire Size (acres, log scale)',
            title='Fire Size vs. Days to Containment',
            yformatter='%.0f',
            hover_cols=['CAUSE', 'FIRE_SIZE', 'DAYS_TO_CONTAIN']
        ).opts(
            tools=['hover'],
            hover_tooltips=[('Category', '@CAUSE'), ('Fire Size (acres)', '@FIRE_SIZE{0,0}'), ('Days to Containment', '@DAYS_TO_CONTAIN')]
        )

    @param.depends('year_range', 'cause_groups')
    def map_chart(self):
        selected = self.cause_groups if self.cause_groups else ['Human', 'Natural', 'Undetermined']
        data = wildfire_sample[
            (wildfire_sample['FIRE_YEAR'] >= self.year_range[0]) &
            (wildfire_sample['FIRE_YEAR'] <= self.year_range[1]) &
            (wildfire_sample['CAUSE'].isin(selected)) &
            (wildfire_sample['LATITUDE'].between(24, 50)) &
            (wildfire_sample['LONGITUDE'].between(-125, -66))
        ]
        return data.hvplot.points(
            x='LONGITUDE', y='LATITUDE', geo=True, tiles='OSM',
            color='CAUSE',
            cmap=cause_colors,
            alpha=0.5, size=6,
            width=CHART_WIDTH, height=CHART_HEIGHT,
            xlabel='Longitude', ylabel='Latitude',
            title='Wildfire Locations (Continental US)',
            hover_cols=['CAUSE', 'STATE', 'FIRE_YEAR']
        ).opts(
            tools=['hover'],
            hover_tooltips=[('Category', '@CAUSE'), ('State', '@STATE'), ('Year', '@FIRE_YEAR')]
        )


dashboard = WildfireDashboard()

# ── Widgets (explicit types, sized to fit the sidebar) ──────
cause_widget = pn.widgets.MultiChoice.from_param(
    dashboard.param.cause_groups,
    name='Cause Category',
    width=230
)
year_widget = pn.widgets.RangeSlider.from_param(
    dashboard.param.year_range,
    name='Year Range',
    width=230
)

# ── Layout ─────────────────────────────────────────────────
layout = pn.template.FastListTemplate(
    title="US Wildfire Dashboard",
    sidebar_width=260,
    sidebar=[
        pn.pane.Markdown("### Filters"),
        cause_widget,
        year_widget
    ],
    main=[
        pn.Row(dashboard.line_chart, dashboard.bar_chart),
        pn.Row(dashboard.scatter_chart, dashboard.map_chart)
    ]
)

layout.servable()