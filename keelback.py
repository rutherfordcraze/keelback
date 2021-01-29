import os, pathlib
import markdown, pystache

DIR_CONTENT     = "Content"
DIR_TEMPLATES   = "Templates"
DIR_EXPORT      = "Export"

###

class Page:
    def __init__(
        self,
        path,
        title
        ):
        self.path = path
        self.title = title
        self.slug = title.lower().replace(" ", "_")

    def __repr__(self):
        return "Page: " + self.slug

    @property
    def content(self):
        with open(os.path.join(self.path, self.title + ".txt"), 'r') as f:
            content = f.read().strip()
        return content

    @property
    def body(self):
        return markdown.markdown(self.content)

    @property
    def crumb(self):
        path = self.path.split("/")
        
        if self.slug == "index":
            crumb = []
        else:
            crumb = [get_link(inventory["index"])]
            for point in path[1:]:
                if point in inventory:
                    crumb.append(get_link(inventory[point]))
        crumb.append(get_link(self, True))

        return " / ".join(crumb)
    

    @property
    def render_props(self):
        return dict(
            vars(self),
            body = self.body,
            crumb = self.crumb)
    

class Category:
    def __init__(
        self,
        title,
        pages = []
        ):
        self.title = title
        self.pages = pages
        self.slug = title.lower().replace(" ", "_")

    def __repr__(self):
        return "Category: " + self.slug

    @property
    def render_props(self):
        return dict(vars(self))

###

def get_inventory():
    inventory = {}

    for path, dirs, files in os.walk(DIR_CONTENT):
        current_dir = path.split('/')[-1]

        if current_dir != "Media":
            inventory[current_dir] = Category(current_dir)
            for file in files:
                if file.endswith(".txt"):
                    title = file[:-4]
                    inventory[title] = Page(path, title)
                    inventory[current_dir].pages.append(inventory[title])

    return inventory

def get_link(page, highlit = False):
    template = "<a href='#{slug}'>{title}</a>"
    if highlit:
        template = "<a href='#{slug}' class='highlit'>{title}</a>"
    return template.format(slug=page.slug, title=page.title)

def render_page(slug):
    if slug not in inventory:
        return "404"
    else:
        page = inventory[slug]

    with open(os.path.join(DIR_TEMPLATES, "page.html"), 'r') as f:
        template = f.read()

    r = pystache.Renderer()
    return r.render(template, page.render_props)

inventory = get_inventory()
# print(inventory)
# print(inventory["Recent Post"].body)
print(render_page("Recent Post"))