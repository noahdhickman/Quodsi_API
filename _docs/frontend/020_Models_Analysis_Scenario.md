
Assume the user has signed in and at their home page or dashboard.

## Model Manager
User can see a list of QuodsiDb Models.  The current web api has api endpoints the return list of models that user can see.  Each model gets its own card where the cards are vertically stacked on top of each other.  each card consumes all the horizontal space.  

The card for models is its own component in its own file.  it is anticipated the design of the card will be heavily iterated on.  

the user can select a model and perform basic crud methods on it.  

One of the most prominent things a user will do is drill into that model's list of analayses in the Analysis Manager

## Analysis Manager
Similar to model, each analysis gets its own card where the cards are vertically stacked on top of each other.  each card consumes all the horizontal space. 

the user can select a analsyis and perform basic crud methods on it.  

a user can select a analsyis and navigate to the Scenario Manager which shows the scenarios of that analysis.

## Scenario Manager
Similar to model and analysis,  each analysis gets its own card where the cards are vertically stacked on top of each other.  each card consumes all the horizontal space. 

the user can select a scenario and perform basic crud methods on it.  

The Scenario Manager will be the most heavily used interface in the application.  Model and Analysis creation will occur but tend to be more one-off tasks to get the user to the Scenario Manager.

Within the ScenarioManager of a Analyses, the user can do the following from a high level
- Run a Scenario
- View results
- View 2d animation of a chosen rep
- Delete, edit, duplicate

Scenarios can be simulated.  There should be a "Animate" button which when pressed will eventually open a new browser tab and feature the ability to see a 2d animation replay of one of the reps.

## Misc
I am trying to design a system that allows user to see Models that were initially created from LucidChart or MIRO.  Said another way, the Standalone version of Quodsi can show data from all sources.  **Source of where the model came from is probably a good database detail we need to include.






