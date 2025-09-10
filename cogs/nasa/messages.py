from config.messages import GlobalMessages


class NasaMess(GlobalMessages):
    nasa_image_brief = "Get NASA image of the day"
    nasa_image_error = "Failed to download NASA image"
    nasa_url = "https://apod.nasa.gov/apod/astropix.html"
