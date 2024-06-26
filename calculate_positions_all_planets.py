from skyfield.api import load
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from skyfield.api import utc
import db_connection as dbconn

# Read about Skyfield here: https://rhodesmill.org/skyfield/planets.html
# Load the planetary ephemeris
eph = load('de421.bsp')

# Define the bodies we're interested in
earth = eph['earth']
sun = eph['sun']
venus = eph['venus']
mars = eph['mars']
jupiter = eph['jupiter barycenter']
saturn = eph['saturn barycenter']


def insert_planet_angles(connection, datetime, venus_angle, mars_angle, jupiter_angle, saturn_angle):
    """
    Inserts planet angles into the PlanetAngles table.

    :param connection: MySQL database connection object
    :param datetime: DateTime object representing the timestamp
    :param venus_angle: Angle of Venus in degrees
    :param mars_angle: Angle of Mars in degrees
    :param jupiter_angle: Angle of Jupiter in degrees
    :param saturn_angle: Angle of Saturn in degrees
    """
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO PlanetAngles (datetime, venus, mars, jupiter, saturn)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (datetime, venus_angle, mars_angle, jupiter_angle, saturn_angle)
        cursor.execute(query, values)
        connection.commit()
        print(f"Planet angles for {datetime} inserted successfully")
    except Error as e:
        print(f"Error while inserting data: {e}")
    finally:
        if cursor:
            cursor.close()


# Function to calculate angle between two vectors. See https://rhodesmill.org/skyfield/coordinates.html
def angle_between(v1, v2):
    v1_u = v1 / np.linalg.norm(v1)
    v2_u = v2 / np.linalg.norm(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


# Function to check if angle is close to 0, 90, or 180 degrees
def check_angle(angle_rad, tolerance_deg=1):
    angle_deg = np.degrees(angle_rad)
    return (abs(angle_deg) < tolerance_deg or
            abs(angle_deg - 90) < tolerance_deg or
            abs(angle_deg - 180) < tolerance_deg)


# Function to plot planet positions
def plot_planets(earth_sun, earth_venus, earth_mars, earth_jupiter, earth_saturn, date):
    plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, projection='polar')

    # Plot Earth-Sun line
    ax.plot([0, 0], [0, 1], 'y-', linewidth=2, label='Earth-Sun')

    # Plot planet positions
    ax.plot([np.angle(earth_venus[0] + 1j * earth_venus[1])], [1], 'ro', markersize=10, label='Venus')
    ax.plot([np.angle(earth_mars[0] + 1j * earth_mars[1])], [1], 'bo', markersize=10, label='Mars')
    ax.plot([np.angle(earth_jupiter[0] + 1j * earth_jupiter[1])], [1], 'go', markersize=10, label='Jupiter')
    ax.plot([np.angle(earth_saturn[0] + 1j * earth_saturn[1])], [1], 'mo', markersize=10, label='Saturn')

    ax.set_ylim(0, 1.2)
    ax.set_yticks([])
    ax.set_theta_zero_location('E')
    ax.set_theta_direction(-1)
    plt.legend(loc='upper left', bbox_to_anchor=(1.1, 1))
    plt.title(f'Planet Positions on {date}')
    plt.tight_layout()
    plt.savefig(f'planet_pos_{date.strftime("%Y%m%d")}.png', dpi=100)
    plt.close()


db_connection = dbconn.create_db_connection()
if not db_connection:
    print("Failed to connect to the database. Exiting.")
    exit()

# Set the time range for calculation
start_date = datetime(1900, 1, 1, tzinfo=utc)
# end_date = start_date + timedelta(days=365)  # Check for one year
end_date = datetime(2035, 12, 31, tzinfo=utc)

# Iterate through dates
current_date = start_date
while current_date <= end_date:
    t = load.timescale().from_datetime(current_date)

    # Calculate positions. See https://rhodesmill.org/skyfield/positions.html
    earth_pos = earth.at(t)
    sun_pos = sun.at(t)
    venus_pos = venus.at(t)
    mars_pos = mars.at(t)
    jupiter_pos = jupiter.at(t)
    saturn_pos = saturn.at(t)

    # Calculate vectors
    earth_sun = sun_pos.position.km - earth_pos.position.km
    earth_venus = venus_pos.position.km - earth_pos.position.km
    earth_mars = mars_pos.position.km - earth_pos.position.km
    earth_jupiter = jupiter_pos.position.km - earth_pos.position.km
    earth_saturn = saturn_pos.position.km - earth_pos.position.km

    # Calculate angles
    venus_angle = angle_between(earth_sun, earth_venus)
    mars_angle = angle_between(earth_sun, earth_mars)
    jupiter_angle = angle_between(earth_sun, earth_jupiter)
    saturn_angle = angle_between(earth_sun, earth_saturn)

    # Check if any planet is at an important angle
    if (check_angle(venus_angle) or check_angle(mars_angle) or
            check_angle(jupiter_angle) or check_angle(saturn_angle)):
        print(f"Date: {current_date}")
        print(f"  Venus angle: {np.degrees(venus_angle):.2f}")
        print(f"  Mars angle: {np.degrees(mars_angle):.2f}")
        print(f"  Jupiter angle: {np.degrees(jupiter_angle):.2f}")
        print(f"  Saturn angle: {np.degrees(saturn_angle):.2f}")
        print()
        if db_connection:
            insert_planet_angles(
                db_connection,
                current_date,
                np.degrees(venus_angle),
                np.degrees(mars_angle),
                np.degrees(jupiter_angle),
                np.degrees(saturn_angle)
            )

        # Generate visualization
        plot_planets(earth_sun[:2], earth_venus[:2], earth_mars[:2], earth_jupiter[:2], earth_saturn[:2], current_date)

    current_date += timedelta(days=1)

db_connection.close()
print("Done.")
