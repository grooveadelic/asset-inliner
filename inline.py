#!/usr/bin/env python3
from sys import argv
from bs4 import BeautifulSoup
from urllib.parse import unquote
from base64 import b64encode
from mimetypes import guess_type


with open(argv[1]) as file_pointer:
    soup = BeautifulSoup(file_pointer, features="lxml")

# remove Content Security Policy meta tag to allow inlining, specifically
# made for Firefox saved pages in readability mode
for meta_tag in soup.head.select('meta'):
    attributes = meta_tag.attrs
    if "http-equiv" in attributes and attributes["http-equiv"] == "Content-Security-Policy":
        meta_tag.extract()

# replace link rel="stylesheet" with embedded stylesheet
for link_tag in soup.head.select('link'):
    attributes = link_tag.attrs
    if "rel" in attributes and attributes['rel'][0] == 'stylesheet':
        relative_stylesheet_location = unquote(link_tag.attrs['href'])
        with open(relative_stylesheet_location) as stylesheet_file:
            stylesheet = stylesheet_file.read()

        # remove link tag
        link_tag.extract()

        style_tag = soup.new_tag("style", type="text/css")
        style_tag.string = stylesheet
        soup.head.append(style_tag)

# replace images with inline base64 encoded images
for image_tag in soup.body.select('img'):
    relative_image_location = unquote(image_tag.attrs['src'])
    with open(relative_image_location, 'rb') as image_file:
        image_binary = image_file.read()

    # Only detect IANA registered mimetypes
    image_mimetype = guess_type(relative_image_location, strict=True)[0]
    inlined_image_src = "data:%s;base64,%s" % (image_mimetype, b64encode(image_binary).decode('UTF-8'))
    
    image_tag.attrs['src'] = inlined_image_src

output_file_name = argv[2] if len(argv) == 1 else 'inlined.html'
with open(output_file_name, 'w') as output_file:
    output_file.write(str(soup))
