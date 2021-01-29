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
        return "page:" + self.slug

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
    def props(self):
        return dict(
            vars(self),
            body = self.body,
            crumb = self.crumb)

    @property
    def html(self):
        with open(os.path.join(DIR_TEMPLATES, "page.html"), 'r') as f:
            template = f.read()

        r = pystache.Renderer()
        return r.render(template, self.props)
    

class Category:
    def __init__(
        self,
        title
        ):
        self.title = title
        self.slug = title.lower().replace(" ", "_")
        self.pages = []

    def __repr__(self):
        return "category:" + self.slug

    def add_page(self, page):
        self.pages.append(page)

    @property
    def crumb(self):
        crumb = [get_link(inventory["index"])]
        crumb.append(get_link(self, True))
        return " / ".join(crumb)

    @property
    def pages_list(self):
        ul = ["<ul>"]
        for page in self.pages:
            ul.append("<li>")
            ul.append(get_link(page))
            ul.append("</li>\n</ul>")
        return '\n'.join(ul)
    

    @property
    def props(self):
        return dict(
            vars(self),
            crumb = self.crumb,
            pages_list = self.pages_list)

    @property
    def html(self):
        with open(os.path.join(DIR_TEMPLATES, "category.html"), 'r') as f:
            template = f.read()

        r = pystache.Renderer()
        return r.render(template, self.props)

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
                    new_page = Page(path, title)
                    inventory[new_page.slug] = new_page
                    print("adding page " + str(new_page) + " to category " + str(current_dir))
                    inventory[current_dir].add_page(new_page)
    return inventory


def get_link(page, highlit = False):
    template = "<a href='/{slug}'>{title}</a>"
    if highlit:
        template = "<a href='/{slug}' class='highlit'>{title}</a>"
    return template.format(slug=page.slug, title=page.title)


def assemble(slug):
    if slug not in inventory:
        return "404"
    elif slug == "" or slug == "/":
        slug = "index"
    page = inventory[slug]
    props = dict(
        page = page.html,
        title = page.title)
    with open(os.path.join(DIR_TEMPLATES, "layout.html"), 'r') as f:
        template = f.read()
    r = pystache.Renderer()
    return r.render(template, props)

def output(slug):
    html = assemble(slug)

    with open(os.path.join(DIR_EXPORT, slug + ".html"), 'w') as f:
        f.write(html)


inventory = get_inventory()
# print(inventory, "\n\n———\n")
# print(assemble("recent_post"), "\n\n———\n")
print(assemble("recent_post"))
output("recent_post")
# print(inventory["Static"].pages)