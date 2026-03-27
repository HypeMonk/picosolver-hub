FLAG = "picoCTF{the_answer_lies_hidden_in_plain_sight}"

def web_solve(params):
    return {
        "success": True,
        "flag": FLAG,
        "log": "[*] m00nwalk2 uses a static flag identical for all instances.\n[SUCCESS] Flag retrieved."
    }

if __name__ == "__main__":
    print(FLAG)
