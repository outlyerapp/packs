# Dataloop Packs

Each pack is comprised of a plugin (Nagios check script), exported dashboard yaml file, exported rules yaml file, a
package description and some help. Each directory in this repo appears as a separate pack in the Dataloop 'Packs Store'
under the Setup page.

To create a new pack fork this repo and then run:

```./create.py <pack name>```

Where `<pack name>` is whatever you want your pack to be called. For now just single words please.

This will create a directory structure like this:

```
example
├── README.md
├── dashboards
│   └── example.yaml
├── package.yaml
├── plugins
│   └── example.py
└── rules
    └── example.yaml
```

When the install button is clicked on each pack in Dataloop it will automatically create a Tag based on the `<pack name>`.
In the example above it would create a Tag called 'example'. It then automatically creates a link between that tag and
all of the plugins in the plugins directory.

The README.md is the help file. Use markdown to describe any configuration changes that need to be in place to get your
pack working. You may also want to describe what the metrics mean on the dashboards and rules.

Paste your exported dashboard yaml content into dashboards/`<pack name>`.yaml but ensure that the scope for every widget
is set to a tag that matches the `<pack name>`.

Update the package.yaml with the following information:

```
title: example
author: steven
version: 1.0.0
description: this is just an example pack
instructions_required: false
icon:
    name: linux
    background: white
    foreground: crimson
```

For the icon you can specify any of the icons in our repo:

http://dataloop.github.io/icons/

Just ignore the .di- in the name.

Paste your plugin content into the plugins/`<pack name>`.py. For now every plugin needs to be written in Python as they
get executed by the Dataloop agent's built Python 2.7 interpreter.

Paste your exported rules yaml content into rules/`<pack name>`.yaml but ensure that the scope for every criteria
is set to a tag that matches the `<pack name>`.

You can add multiple plugins, dashboards and rules to a pack if you'd like to split stuff out a bit. Every plugin will
get linked to the Tag that matches the `<pack name>`.

Once you've done all of the above submit a pull request and earn your place in the halls of monitoring fame.
