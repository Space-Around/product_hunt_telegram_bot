def bold(text):
    return "*" + str(text) + "*" 


def italic(text):
    return "_" + str(text) + "_" 


def prepare_markdown(text):
   new_text = text
   new_text = new_text.replace(".", "\.")
   new_text = new_text.replace("-", "\-")
   new_text = new_text.replace("!", "\!")
   new_text = new_text.replace("=", "\=")
   new_text = new_text.replace("+", "\+")
   new_text = new_text.replace("(", "\(")
   new_text = new_text.replace(")", "\)")
   new_text = new_text.replace("#", "\#")
   new_text = new_text.replace("<", "\<")
   new_text = new_text.replace(">", "\>")
   new_text = new_text.replace("]", "\]")
   new_text = new_text.replace("[", "\[")

   return new_text