# Keelback

> __This is not ‘good’ software.__
> You are free to use it, but please bear in mind it’s a janky personal project. It might not work the way you want it to. It might not work at all.

## About

Keelback is a flat-file static site builder written in Python. It’s designed to make categorising and maintaining the source content straightforward, while keeping a wiki-like (non-hierarchic) link structure.

Content is stored in txt files and rendered using Markdown, with templates written in html and rendered with Pystache. Static objects like stylesheets and images are not modified.

## Usage

### Installation

Create a virtual environment and activate it:
```
$ python3 -m venv .venv
$ source .venv/bin/activate
```

Install the requirements:
```
$ pip install -r requirements.txt
```

### Export

The `config.json` file contains a few configurable settings, like the content and export directories. When you’ve made the desired changes, run Keelback:
```
$ python3 keelback.py
```

(If the export folder doesn’t exist, you may need to create it first. Please note that anything in this folder will be overwritten.)

## Hierarchy

Pages can be categorised by arranging them in folders within the content directory. On export, the hierarchy is flattened and category pages are generated automatically for each folder. If a `txt` file exists with the same name as a category, it will overwrite the auto-generated category page.

The following content structure:

    Content/
      ├─ index.txt
      ├─ 404.txt
      │  ...
      └─ recipes/
           ├─ risotto.txt
           └─ tortellini.txt
              ...

will be exported as:

    Export/
      ├─ index.html
      ├─ 404.html
      ├─ recipes.html
      ├─ risotto.html
      └─ tortellini.html
         ...

with the file `recipes.html` generated automatically, containing a linked list of every `html` file in the ‘recipes’ category.

## Metadata

Pages can optionally include metadata, in the form of key-value pairs (one per line), separated from the main content by a delimiter (`=====` by default).

    Title: Example Blog Post
    Date: 01-09-2021
    =====
    ...

Only `title` and `date` are used by Keelback: `title` overrides the page’s filename (since the latter must also work as a URL slug), and `date` is used to sort time-based content like blog posts.


## Dynamic Content

Pages are rendered using [Pystache](https://github.com/defunkt/pystache), a Python implementation of the [Mustache](http://mustache.github.io) logicless template system. This can also be used within page content to access other page and category objects within the site:

- `pages.<slug>.link` returns a link to the specified page, with the page’s `title` attribute as the link text.

- `pages.<slug>.meta.<property>` returns arbitrary metadata for the specified page (as described above).

- `categories.<name>.contents` returns an `html` list of all pages in the specified category. If every page in the category has a `date` attribute, this list is an `ol` in reverse chronological order; otherwise it’s an alphabetically sorted `ul`.