from enum import Enum

TokenValue = Enum(
    'TokenValue',
    [
        'LEFT_PAREN',       # (
        'RIGHT_PAREN',      # )
        'LEFT_BRACE',       #
        'RIGHT_BRACE',      #
        'LEFT_BRACKET',     #
        'RIGHT_BRACKET',    #
        'EQUAL',            #
        'PLUS',             #
        'PLUSPLUS',         #
        'MINUS',            #
        'MINUSMINUS',       #
        'STAR',             #
        'DOT',              #
        'SLASH',            #
        'BANG',             #
        'GREATER',          #
        'LESS',             #
        'BANG_EQUAL',       #
        'GREATER_EQUAL',    #
        'LESS_EQUAL',       #
        'EQUAL_EQUAL',      #
        'COMMA',            #
        'SEMICOLON',        #
        'IDENTIFIER',       #
        'NEW',              # var
        'STRING',           #
        'NUMBER',           #
        'TRUE',             #
        'FALSE',            #
        'SLOTH',            # class
        'NULL',             # nil
        'AND',              # and
        'OR',               # or
        'IF',               # if
        'ELSE',             # else
        'WHILE',            # while
        'FOR',              # for
        'PRINT',            # print
        'GIVE',             # return
        'SUPER',            # 
        'THIS',             # 
        'FUN',              # function
        'EOF'               # END OF FILE
    ]
)