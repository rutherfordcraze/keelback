import os, pathlib, time
import markdown, pystache
from datetime import datetime

DIR_CONTENT     = "Content"
DIR_TEMPLATES   = "Templates"
DIR_EXPORT      = "Export"

###

class Page:
    def __init__(
        self,
        path,
        title,
        ctime = None
        ):
        self.path = path
        self.title = title
        self.slug = title.lower().replace(" ", "_")
        self.ctime = ctime

    def __repr__(self):
        return "page:" + self.slug

    @property
    def content(self):
        with open(os.path.join(self.path, self.title + ".txt"), 'r') as f:
            content = f.read().strip()
        return content

    @property
    def body(self):
        template = markdown.markdown(self.content)
        r = pystache.Renderer()
        return r.render(template, dict(categories=get_categories()))

    @property
    def timestamp(self):
        if self.ctime:
            return datetime.utcfromtimestamp(self.ctime).strftime('%b %Y')
        return None
    

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
            crumb = self.crumb,
            timestamp = self.timestamp)

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
    def contents(self):
        ul = ["<ul>"]
        for page in self.pages:
            ul.append("<li>")
            ul.append(get_link(page))
            if page.timestamp:
                ul.append("<span class='timestamp'>")
                ul.append(page.timestamp)
                ul.append("</span>")
            ul.append("</li>")
        ul.append("</ul>")
        return '\n'.join(ul)
    

    @property
    def props(self):
        return dict(
            vars(self),
            crumb = self.crumb,
            contents = self.contents)

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
        if current_dir != "media":
            if current_dir != "Content":
                inventory[current_dir] = Category(current_dir)
            for file in files:
                if file.endswith(".txt"):
                    title = file[:-4]
                    
                    if current_dir == "posts":
                        fname = pathlib.Path(os.path.join(path, file))
                        ctime = int(fname.stat().st_ctime)
                    else:
                        ctime = None

                    new_page = Page(path, title, ctime)
                    inventory[new_page.slug] = new_page

                    if current_dir != "Content":
                        inventory[current_dir].add_page(new_page)
    return inventory


def get_categories():
    if inventory:
        categories = {}
        for k, v in inventory.items():
            value_type = v.__class__.__name__
            if value_type == "Category":
                categories[k] = v

        return categories


def get_link(page, highlit = False):
    template = "<a href='/{slug}.html'>{title}</a>"
    if highlit:
        template = "<a href='/{slug}.html' class='highlit'>{title}</a>"
    return template.format(slug=page.slug, title=page.title)


def assemble(slug):
    if slug not in inventory:
        return "404"
    elif slug == "" or slug == "/":
        slug = "index"

    page = inventory[slug]
    props = dict(page = page.html, title = page.title)

    with open(os.path.join(DIR_TEMPLATES, "layout.html"), 'r') as f:
        template = f.read()

    r = pystache.Renderer()
    return r.render(template, props)


def output(slug):
    html = assemble(slug)

    with open(os.path.join(DIR_EXPORT, slug + ".html"), 'w') as f:
        f.write(html)


def output_all():
    counter = 0
    start = time.time()
    for slug in inventory.keys():
        output(slug)
        counter += 1
    stop = time.time()
    elapsed = int((stop - start) * 1000)

    print("[KEELBACK] Exported {pages} pages in {time} ms.".format(
        pages=counter,
        time=elapsed))


inventory = get_inventory()
output_all()