from enum import Enum
import json

class Resource(Enum):
    SALVAGE = 0
    COAL = 1
    COMP = 2
    DCOMP = 3
    SULFUR = 4
    EMAT = 5
    HEMAT = 6
    CONCRETE = 7
    OIL = 8
    PETROL = 9
    WATER = 10
    COKE = 11
    HOIL = 12
    EOIL = 13
    CMAT = 14
    PCON = 15
    SCON = 16
    AMAT1 = 17
    AMAT2 = 18
    AMAT3 = 19
    AMAT4 = 20
    AMAT5 = 21
    SANDBAG = 22
    BWIRE = 23
    MBEAM = 24
    FLAME = 25  # Flame Ammo
    A250 = 26   # Cannot start with number
    A75 = 27
    A945 = 28
    A300 = 29
    A120 = 30
    A150 = 31
    HEROCKET = 32
    FIREROCKET = 33
    PIPE = 34
    GSUPP = 35

def formatFloat(float) -> str:
    return ('%.2f' % float).rstrip('0').rstrip('.')

def isfloat(num) -> bool:
    try:
        float(num)
        return True
    except ValueError:
        return False

def isint(input) -> bool:
    try:
        int(input)
        return True
    except ValueError:
        return False

class ResourceTuple:
    def __init__(self, amount: float, resource: Resource):
        self.amount = amount
        self.resource = resource

    def resourceStr(self) -> str:
        return self.resource.name

class MonoRecipe:
    # A recipe with one output, any number of side outputs and any number of inputs
    def __init__(self, output: Resource, inputs: list[ResourceTuple], sideOutputs: list[ResourceTuple]):
        self.output = output
        self.inputs = inputs
        self.sideOutputs = sideOutputs

    def __str__(self):
        # FORMAT: 3 CMAT + 20 COMP -> 1 PCON + 1 MBEAM

        result = str(formatFloat(self.inputs[0].amount)) + ' ' + self.inputs[0].resourceStr()
        if len(self.inputs) > 1:
            for i in range(1, len(self.inputs)):
                result += ' + ' + str(formatFloat(self.inputs[i].amount)) + ' ' + self.inputs[i].resourceStr()

        result += ' -> 1' + ' ' + self.output.name

        for sideOut in self.sideOutputs:
            result += ' + ' + str(formatFloat(sideOut.amount)) + ' ' + sideOut.resourceStr()

        return result

class RecipeList:
    def __init__(self):
        self.recipes:list[MonoRecipe] = []

    def readRecipes(self, file: str):
        recipeFile = open(file)
        recipeDict = json.load(recipeFile)

        for recipe in recipeDict['recipes']:
            for output in recipe['outputs']:
                # For each output in the recipe, we create a mono recipe.
                monoOutput = Resource[output['name'].upper()]
                monoDivisor = output['amount']
                monoSides = []
                monoInputs = []

                for sideOut in recipe['outputs']:
                    if sideOut['name'] != output['name']:
                        monoSides.append(ResourceTuple(sideOut['amount'] / monoDivisor, Resource[sideOut['name'].upper()]))

                for input in recipe['inputs']:
                    monoInputs.append(ResourceTuple(input['amount'] / monoDivisor, Resource[input['name'].upper()]))
                
                self.recipes.append(MonoRecipe(monoOutput, monoInputs, monoSides))
    
    def findRecipes(self, output: Resource) -> list[MonoRecipe]:
        result = []
        for recipe in self.recipes:
            if recipe.output == output:
                result.append(recipe)
        return result

class RecipeCalculator:
    def __init__(self, recipeList: RecipeList):
        self.recipeList = recipeList
    
    def calculateRecipe(self, outputList: list[ResourceTuple]) -> dict:
        excessDict = {}
        for output in outputList:
            excessDict[output.resourceStr()] = 0-output.amount

        for output in outputList:
            self.calcRecursive(output.resource, excessDict)

        print('\n' * 150)
        print('Producing:')
        for output in outputList:
            print(formatFloat(output.amount), output.resourceStr())

        RecipeCalculator.printResult(excessDict)

    def calcRecursive(self, output: Resource, excessDict: dict):
        # Ensures that we need at least one of output
        if excessDict[output.name] < 0:
            numNeeded = 0 - excessDict[output.name]

            recipeCandidates = self.recipeList.findRecipes(output)
            if len(recipeCandidates) != 0:
                chosenNum = RecipeCalculator.printOptions(recipeCandidates, output)

                if chosenNum != 0:
                    excessDict[output.name] = 0

                    for sideOutput in recipeCandidates[chosenNum-1].sideOutputs:
                        # Adds an excess of the side product to the excess dictionary
                        if sideOutput.resourceStr() in excessDict:
                            excessDict[sideOutput.resourceStr()] += sideOutput.amount*numNeeded
                        else:
                            excessDict[sideOutput.resourceStr()] = sideOutput.amount*numNeeded

                    for input in recipeCandidates[chosenNum-1].inputs:
                        if input.resourceStr() in excessDict:
                            excessDict[input.resourceStr()] -= input.amount*numNeeded
                        else:
                            excessDict[input.resourceStr()] = 0-(input.amount*numNeeded)
                        
                        self.calcRecursive(input.resource, excessDict)

    def printResult(excessDict: dict):
        print('\nMaterials:')
        for resource in sorted(excessDict.items()):
            if resource[1] < 0:
                print(formatFloat(0-resource[1]), resource[0])

        print('\nByproducts:')
        for resource in sorted(excessDict.items()):
            if resource[1] > 0:
                print(formatFloat(resource[1]), resource[0])

    def printOptions(recipes: list, output: Resource) -> int:
        print('\n' * 150)
        print('Select', output.name, 'recipe:\n\n0.    NONE')

        for i in range(1, len(recipes)+1):
            print(i, '.    ', recipes[i-1], sep='')

        print('\nEnter a number: ', end='')
        return int(input())

def getProducts() -> list[ResourceTuple]:
    productList:list[ResourceTuple] = []
    print('\n' * 150)
    print('Enter number of products: ', end='')
    line = input()

    while not isint(line):
        print('\n' * 150)
        print('Input Invalid.')
        print('Enter number of products: ', end='')
        line = input()

    for i in range(int(line)):
        print('\n' * 150)
        print('Enter product in form "NUMBER NAME":')
        values = input().split(' ')
        
        values = productValidation(values)

        productList.append(ResourceTuple(float(values[0]), Resource[values[1].upper()]))

    return productList

def productValidation(values: list) -> list:
    changeValues(values)
    while (len(values) < 2) or (not isfloat(values[0])) or (values[1].upper() not in Resource.__members__):
        print('\n' * 150)

        if len(values) < 2:
            print('Input Invalid: Not enough input.')
        elif not isfloat(values[0]):
            print('Input Invalid: First value not a number.')
        elif values[1].upper() not in Resource.__members__:
            print('Input Invalid: Material "', values[1], '" not found.', sep="")

        print('Enter product in form "NUMBER NAME":')
        values = input().split(' ')
        changeValues(values)

    return values

def changeValues(values: list[str]):
    if len(values) > 1:
        # Changes values to match Resource Enum format
        if 'MM' in values[1].upper():
            values[1] = values[1].upper().replace('MM', '')
            values[1] = 'A' + values[1]

        if values[1] == 'A94.5':
            values[1] = 'A945'

        if '3C' in values[1].upper():
            values[1] = 'HEROCKET'
        elif '4C' in values[1].upper():
            values[1] = 'FIREROCKET'

if __name__ == '__main__':
    recipeList = RecipeList()
    recipeList.readRecipes('recipes.json')

    calc = RecipeCalculator(recipeList)

    productList = getProducts()
    calc.calculateRecipe(productList)