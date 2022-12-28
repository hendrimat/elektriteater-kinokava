from bs4 import BeautifulSoup
from ics import Calendar, Event
import urllib.request
import ssl
import arrow
from datetime import timedelta

# Funktsioon get_html_data võtab lehe url'i ning tagastab selle lehe BeautifulSoup'i objekti.
def get_html_data(url):
    with urllib.request.urlopen(
        url, context=ssl._create_unverified_context()
    ) as response:
        html = response.read()
    return BeautifulSoup(html, "html.parser")

# Muutujad "url" ja "filename"
url = "https://elektriteater.ee/"
filename = "elektriteater_" + arrow.now().format("YYYY-MM-DD") + ".ics"

# Loome kalendri ja otsime kinokava info lehelt.
calendar = Calendar()
session_list = get_html_data(url).find_all(class_="session-list__item")

# Teeme kalendri sündmuse iga seansi jaoks.
for session_data in session_list:
    calendar_event = Event()

    # Leiame filmi pealkirja ja lisame sellele programmi nime, kui see on olemas.
    title = session_data.find(class_="session-list__title").string
    program = session_data.find(class_="session-list__program")
    if program != None:
        title += " (" + program.string + ")"
    calendar_event.name = title

    # Lisame kalendri sündmuse kirjeldusse filmi lingi.
    link = session_data.find(class_="session-list__item-link")["href"]
    calendar_event.description = link

    # Leiame alguse kuupäeva.
    date_start = arrow.get(session_data["data-date"], "YYYYMMDD")

    # Kui seansi kellaaeg on olemas siis on tegemist tavalise seansiga, aga kui ei leidu siis on tegemist programmiga.
    time = session_data.find(
        class_="session-list__date-item session-list__date-item--time"
    )
    if time != None:
        # Leiame seansi algusaja.
        date_time = date_start.format("YYYY-MM-DD") + " " + time.string
        date_time_begin = arrow.get(date_time)
        calendar_event.begin = date_time_begin

        # Otsime filmi lehelt seansi pikkust.
        duration = (
            get_html_data(link)
            .find(class_="film__content")
            .next_sibling.string.split(", ")[-1]
        )
        # Määrame seansi pikkuse.
        if "h" in duration:
            duration = duration.split("h ")
            duration = timedelta(
                hours=int(duration[0]), minutes=int(duration[1].strip("m"))
            )
        else:
            duration = timedelta(minutes=int(duration.strip("m")))
        calendar_event.duration = duration
    else:
        # Leiame programmi algus- ja lõppkuupäevad.
        date_range = session_data.find(
            class_="session-list__date-item session-list__date-item--date"
        ).string.split(" - ")
        date_end = arrow.get(
            date_range[-1] + " " + str(date_start.year),
            "D. MMMM YYYY",
            locale="ee",
        )
        calendar_event.begin = date_start
        calendar_event.end = date_end
        calendar_event.make_all_day()

    # Lisame sündmuse kalendrisse.
    calendar.events.add(calendar_event)

# Kirjutame kalendri faili.
with open(filename, "w") as f:
    f.writelines(calendar.serialize_iter())
