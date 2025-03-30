""""Nuke panel for building vfx shot review blocks"""


import os

import shot_review_import_loader
import filesystem_parser
import user_preferences


import nuke
import nukescripts


PANEL_IDENTIFIER = "com.flawlessai.vfx.shotreviewimportpanel"

# The following first defines a new class called ImportReview.
class ImportReview( nukescripts.PythonPanel ):

  def __init__( self ) -> nukescripts.PythonPanel:
    nukescripts.PythonPanel.__init__( self, "ShotReviewImporter", PANEL_IDENTIFIER)

    self.shows_knob = nuke.Enumeration_Knob( "show", "Show:", [])
    self.addKnob( self.shows_knob )

    self.episode_knob = nuke.Enumeration_Knob( "episode", "Episode:", [])
    self.addKnob( self.episode_knob )

    self.part_knob = nuke.Enumeration_Knob( "part", "Part:", [])
    self.addKnob( self.part_knob )

    self.shot_knob = nuke.Enumeration_Knob( "shot", "Shot:", [])
    self.addKnob( self.shot_knob )

    self.language_knob = nuke.Enumeration_Knob( "language", "Language:", [])
    self.addKnob( self.language_knob )

    self.variant_knob = nuke.Enumeration_Knob( "variant", "Variant:", [])
    self.addKnob( self.variant_knob )

    self.load_reviewables = nuke.PyScript_Knob( "import", "Import:", "shot_review_import_ui.import_reviewable()")
    self.load_reviewables.setFlag(nuke.STARTLINE)
    self.addKnob( self.load_reviewables )

    self.update_shows()

  def update_shows(self) -> None:
    """Show parameter initializer"""
    active_shows = filesystem_parser.get_shows()
    self.shows_knob.setValues(active_shows)
    show = user_preferences.get("show")
    if show in active_shows:
      self.shows_knob.setValue(show)
      self.knobChanged(self.shows_knob)

  def knobChanged( self, knob: nuke.Knob ) -> None:
    """Knob Change event handler"""
    if knob == self.shows_knob:
      show_selected = self.shows_knob.value()
      self.episode_knob.setValues(
        filesystem_parser.get_episodes(show_selected)
      )
      user_preferences.set("show", show_selected)
      self.knobChanged(self.episode_knob)
    if knob == self.episode_knob:
      show = self.shows_knob.value()
      episode = self.episode_knob.value()
      parts = filesystem_parser.get_parts(show, episode)
      self.part_knob.setValues(parts)
      self.knobChanged(self.part_knob)
    if knob == self.part_knob:
      show = self.shows_knob.value()
      episode = self.episode_knob.value()
      part = self.part_knob.value()
      shots = filesystem_parser.get_shots(show, episode, part)
      self.shot_knob.setValues(shots)
      self.knobChanged(self.shot_knob)
    if knob == self.shot_knob:
      show = self.shows_knob.value()
      episode = self.episode_knob.value()
      part = self.part_knob.value()
      shot = self.shot_knob.value()
      languages = filesystem_parser.get_languages(show, episode, part, shot)
      languages.append("all")
      self.language_knob.setValues(languages)
      self.language_knob.setValue("all")
      self.knobChanged(self.language_knob)
    if knob == self.language_knob:
      show = self.shows_knob.value()
      episode = self.episode_knob.value()
      part = self.part_knob.value()
      shot = self.shot_knob.value()
      language = self.language_knob.value()
      variants = filesystem_parser.get_variants(show, episode, part, shot, language)
      variants.append("all")
      self.variant_knob.setValues(variants)
      self.variant_knob.setValue("all")

def get_context( panel: nuke.Panel ) -> dict:
  """Convert panel parameters into context"""
  all_knobs = panel.knobs()
  return {
    "show": all_knobs["show"].value(),
    "episode": all_knobs["episode"].value(),
    "part": all_knobs["part"].value(),
    "shot": all_knobs["shot"].value(),
    "language": all_knobs["language"].value(),
    "variant": all_knobs["variant"].value()
  }


def import_reviewable() -> None:
  """Review block build trigger"""
  knob = nuke.thisKnob()
  panel = knob.node()

  context = get_context(panel)
  shot_review_import_loader.review_shot(**context)


def add_panel() -> nuke.Panel:
  """New Panel constructor"""
  return ImportReview().addToPane()


nukescripts.registerPanel(PANEL_IDENTIFIER, add_panel)

