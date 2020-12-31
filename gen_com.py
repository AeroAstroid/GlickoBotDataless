command_name = input("Command name: ")
aliases = input("Aliases: ")

with open('Functions/command_template.txt', 'r', encoding='utf-8') as f:
	code = f.read()
	
	code = code.replace("<COMMAND NAME>", command_name.lower())

	if aliases != "":
		aliases = str(aliases.split(" "))
		code = code.replace("<ALIASES>", f", aliases={aliases}")
	
	else:
		code = code.replace("<ALIASES>", "")

with open(f'Commands/{command_name.lower()}.py', 'w', encoding='utf-8') as f:
	f.write(code)