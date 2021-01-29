import os, pathlib
import markdown

DIR_CONTENT     = "Content"
DIR_TEMPLATES   = "Templates"
DIR_EXPORT      = "Export"

###

class Page:
    def __init__(
        self,
        path,
        slug,
        content = None
        ):
        self.slug = slug
        self.path = path
        self.content = content

    def __repr__(self):
        return "Page: " + self.slug

    def body(self):
        if self.content:
            return markdown.markdown(self.content)
        return None

class Category:
    def __init__(
        self,
        slug,
        pages = []
        ):
        self.slug = slug
        self.pages = pages

    def __repr__(self):
        return "Category: " + self.slug

###

def get_inventory():
    inventory = {}

    for path, dirs, files in os.walk(DIR_CONTENT):
        current_dir = path.split('/')[-1]

        if current_dir != "Media":
            for file in files:
                if file.endswith(".txt"):
                    if current_dir not in inventory:
                        inventory[current_dir] = []
                    inventory[current_dir].append(Page(path, file[:-4]))

    return inventory