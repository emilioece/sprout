# ===========================================================================
# Dashboard Page View
# ===========================================================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from theme import theme

def render_dashboard(app):
    """Renders either the main dashboard overview or the welcome empty state."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    # If the user has no plants saved, show the empty welcome view
    if not app.plants:
        app.render_empty_state()
        return

    # Header section for active collection
    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(
        text="Dashboard", bold=True, font_size="30sp",
        color=theme.text, halign="left", size_hint_y=None, height=dp(40)
    ))
    header.add_widget(Label(
        text="Overview of your current plant status", font_size="12sp",
        color=theme.muted, halign="left", size_hint_y=None, height=dp(18)
    ))
    container.add_widget(header)

    from main import StatCard, PlantRow

    # Calculate statistics based on plant care dates
    overdue = sum(1 for p in app.plants if p.get("daysUntilWater", 0) < 0)
    due_today = sum(1 for p in app.plants if p.get("daysUntilWater", 0) == 0)

    # Top statistics cards row
    stats_row = BoxLayout(size_hint_y=None, height=dp(120), spacing=dp(16))
    stats_row.add_widget(StatCard(icon="\U0001FAB4", value=str(len(app.plants)), label_text="Plants"))
    stats_row.add_widget(StatCard(icon="\u26A0\uFE0F", value=str(overdue), label_text="Overdue tasks"))
    stats_row.add_widget(StatCard(icon="\U0001F4CB", value=str(due_today), label_text="Due today"))
    container.add_widget(stats_row)

    # Section title
    container.add_widget(Label(
        text="Upcoming watering", bold=True, font_size="18sp",
        color=theme.text, halign="left", size_hint_y=None, height=dp(30)
    ))

    # List of plant rows
    list_box = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
    list_box.bind(minimum_height=list_box.setter("height"))

    for plant in app.plants:
        name = plant.get("name") or plant.get("nickname", "")
        row = PlantRow(
            plant_id=plant.get("id"),
            plant_name=name,
            subtitle=plant.get("location") or plant.get("species") or "Unspecified",
            initials=(name[:4] if name else ""),
            due_label=f"In {plant.get('daysUntilWater', 0)}d",
        )
        row.on_water_cb = app.water_plant
        row.on_delete_cb = app.open_delete_modal
        list_box.add_widget(row)

    container.add_widget(list_box)