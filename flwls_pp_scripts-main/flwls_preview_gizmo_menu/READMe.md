# Welcome to the Flawless Preview Gizmo Menu

## What is this for?

The Flawless Preview Gizmo Menu is a directory used for sharing and testing nuke Gizmos and Toolsets before they're added permenently to `flwls_pp_scripts`.

### Sharing Gizmos, Nodes and ToolSets 

When working on a show, a user may have a particual setup that can be used on multiple shots within a sequence/show. This could be as little as one node. Adding these tools/setups to the FPGM is a great way to share these with other artists. Bear in mind that this is temporary. When a show wraps, it is reccomended that artists remove anything they have added. 

### Testing/Previewing Gizmos

When downloading a new Gizmo from a site like NukePedia, the FPGM can be used as a preview environment. The Gizmo can be placed into the menu while we ascertain if the tool should become a permenant part of our pipeline (placed into the main Flawless ToolBar menu). 
This is also the same for custom tools created by artists internally. 

Remember, this is not a safe place to store files. Anyone can modify these files.


## How to format Gizmos, Groups and Toolsets for use within the Menu

All gizmos must be converted to Groups before being added to the menu. The following insturctions can be followed for Gizmos, Groups and ToolSets. 

### Preparing Groups

Inside the Menu, pressing the item named `Gizmo Dir` will reveal a path to a directory. For a Tool to be visible inside the menu, it needs to be added to that directory. 

When preparing tools for the menu, please follow these steps:

 - Copy the Gizmo/Group/Node/Toolset into a text editor.
 
 - Remove the following text from the document: (Skip this step when prepping ToolSets.)


            set cut_paste_input [stack 0]
            version 13.1 v2
            push $cut_paste_input


            xpos 174
            ypos -15

    (Only remove the `xpos` and `ypos` for the Group, not all the nodes within the group.)

 - Save this text document into an appropraitely named folder within the directory named `Flawless_Preview_Gizmo_Menu`. 

    (Do not put the Group/Gizmo/Toolset directly into the `Flawless_Preview_Gizmo_Menu`, it must be in a subfolder.)

### Naming Conventions (For Internally created Gizmos/Tools only)

When saving your Gizmo, please use underscores or uppercase lettering to indicate the start of a new word. Use the file extension `.gizmo`.
For example, a Gizmo named `my gizmo`, should be formatted as either `MyGizmo.gizmo` or `my_gizmo.gizmo`. 

## Requesting an addition to the main Flawless Toolbar Menu

After Previewing a Gizmo/Tool in the Preview Menu, a ticket can be created requesting that this Gizmo should be added to the permenent Toolbar Menu. 

### Creating the ticket

 - A Gizmo request ticket should be added to the TPS Jira Board.
 - Leave the asignee as unassinged.
 - Please include any documentation that can assist with installing the tool (for example, NukePedia docuemtnation).
 - Inlcude download links/paths where this tool can be located. If you've already converted the tool to a group, please include this location as part of the ticket.
 - Suggest which subfolder the tool should be added to (Draw, Colour, Transform etc).
 - Message the innovation team in the vfx_pipeline Slack channel, making sure to include a link to the Jira ticket. 

Make sure you have tested this tool first, either on your own workstation, or in the Preview Menu.

## Additional notes and considerations 

 - If a new item is added to the menu, nuke will have to be restarted for users to see this additonal item.  
 - Remember, these tools are visible to everyone. Only include tools that others will find useful.
 - Anyone can add or delete items here. Keep copies of these tools. 
 - If you are not able to see the menu item in nukes toolbar, someone may have deleted or renamed the `Flawless_Preview_Gizmo_Menu` directory.
 - Even this README could be deleted. Please inform VFX pipeline if anything doesn't appear to be working. 


