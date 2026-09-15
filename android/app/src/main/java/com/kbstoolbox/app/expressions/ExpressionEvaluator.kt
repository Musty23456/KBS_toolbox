package com.kbstoolbox.app.expressions

/**
 * A small, restricted expression evaluator for `relevance_expression` /
 * `calculation_expression`, mirroring the backend's safe subset
 * (app/services/expressions.py) so the form behaves identically whether
 * evaluated online or offline: comparisons, and/or, +-* /, string and
 * numeric literals, and bare variable names referencing other questions by
 * their `code`. No function calls, no attribute access — this is a small
 * hand-rolled tokenizer/parser, not Kotlin's own evaluator, so there is no
 * way for a survey author's expression to execute arbitrary code.
 */
object ExpressionEvaluator {

    fun isRelevant(expression: String?, answers: Map<String, Any?>): Boolean {
        if (expression.isNullOrBlank()) return true
        return try {
            toBoolean(evaluate(expression, answers))
        } catch (e: ExpressionException) {
            // Fail open: a broken rule must never hide a question from the
            // field, only a working one may.
            true
        }
    }

    fun evaluate(expression: String, variables: Map<String, Any?>): Any? {
        val tokens = Lexer(expression).tokenize()
        val parser = Parser(tokens, variables)
        val result = parser.parseExpression()
        parser.expectFullyConsumed()
        return result
    }

    private fun toBoolean(value: Any?): Boolean = when (value) {
        null -> false
        is Boolean -> value
        is Number -> value.toDouble() != 0.0
        is String -> value.isNotEmpty()
        else -> true
    }

    class ExpressionException(message: String) : Exception(message)

    private sealed class Token {
        data class Ident(val name: String) : Token()
        data class NumberLit(val value: Double) : Token()
        data class StringLit(val value: String) : Token()
        data class Op(val symbol: String) : Token()
        data object End : Token()
    }

    private class Lexer(private val input: String) {
        private var pos = 0

        fun tokenize(): List<Token> {
            val tokens = mutableListOf<Token>()
            while (pos < input.length) {
                val c = input[pos]
                when {
                    c.isWhitespace() -> pos++
                    c == '\'' || c == '"' -> tokens.add(readString(c))
                    c.isDigit() -> tokens.add(readNumber())
                    c.isLetter() || c == '_' -> tokens.add(readIdentOrKeyword())
                    else -> tokens.add(readOperator())
                }
            }
            tokens.add(Token.End)
            return tokens
        }

        private fun readString(quote: Char): Token {
            pos++ // skip opening quote
            val start = pos
            while (pos < input.length && input[pos] != quote) pos++
            val value = input.substring(start, pos)
            if (pos < input.length) pos++ // skip closing quote
            return Token.StringLit(value)
        }

        private fun readNumber(): Token {
            val start = pos
            while (pos < input.length && (input[pos].isDigit() || input[pos] == '.')) pos++
            return Token.NumberLit(input.substring(start, pos).toDouble())
        }

        private fun readIdentOrKeyword(): Token {
            val start = pos
            while (pos < input.length && (input[pos].isLetterOrDigit() || input[pos] == '_')) pos++
            return Token.Ident(input.substring(start, pos))
        }

        private fun readOperator(): Token {
            val twoChar = input.substring(pos, minOf(pos + 2, input.length))
            if (twoChar in listOf("==", "!=", ">=", "<=")) {
                pos += 2
                return Token.Op(twoChar)
            }
            val oneChar = input[pos].toString()
            pos++
            return Token.Op(oneChar)
        }
    }

    /** Simple recursive-descent parser evaluating directly as it parses (no separate AST). */
    private class Parser(private val tokens: List<Token>, private val variables: Map<String, Any?>) {
        private var pos = 0
        private fun peek() = tokens[pos]
        private fun advance() = tokens[pos++]

        /**
         * The recursive-descent parser below stops as soon as it has parsed
         * one full expression — it never independently checks that every
         * token was consumed. Malformed input like "this is not valid (((”
         * would otherwise parse just its first token as a bare variable
         * reference and silently ignore the unparseable remainder instead
         * of raising an error, which would make evaluate() return a
         * misleadingly "successful" null rather than the ExpressionException
         * that lets isRelevant() fail open correctly.
         */
        fun expectFullyConsumed() {
            if (peek() !is Token.End) {
                throw ExpressionException("Unexpected trailing input in expression")
            }
        }

        fun parseExpression(): Any? = parseOr()

        private fun parseOr(): Any? {
            var left = parseAnd()
            while (peek() is Token.Ident && (peek() as Token.Ident).name == "or") {
                advance()
                val right = parseAnd()
                left = toBool(left) || toBool(right)
            }
            return left
        }

        private fun parseAnd(): Any? {
            var left = parseNot()
            while (peek() is Token.Ident && (peek() as Token.Ident).name == "and") {
                advance()
                val right = parseNot()
                left = toBool(left) && toBool(right)
            }
            return left
        }

        private fun parseNot(): Any? {
            if (peek() is Token.Ident && (peek() as Token.Ident).name == "not") {
                advance()
                return !toBool(parseNot())
            }
            return parseComparison()
        }

        private fun parseComparison(): Any? {
            val left = parseArithmetic()
            val op = peek()
            if (op is Token.Op && op.symbol in listOf("==", "!=", ">", "<", ">=", "<=")) {
                advance()
                val right = parseArithmetic()
                return compare(left, op.symbol, right)
            }
            return left
        }

        private fun parseArithmetic(): Any? {
            var left = parseTerm()
            while (peek() is Token.Op && (peek() as Token.Op).symbol in listOf("+", "-")) {
                val op = (advance() as Token.Op).symbol
                val right = parseTerm()
                left = if (left == null || right == null) null
                else if (op == "+") toNum(left) + toNum(right) else toNum(left) - toNum(right)
            }
            return left
        }

        private fun parseTerm(): Any? {
            var left = parseFactor()
            while (peek() is Token.Op && (peek() as Token.Op).symbol in listOf("*", "/")) {
                val op = (advance() as Token.Op).symbol
                val right = parseFactor()
                left = if (left == null || right == null) null
                else if (op == "*") toNum(left) * toNum(right) else toNum(left) / toNum(right)
            }
            return left
        }

        private fun parseFactor(): Any? {
            return when (val token = peek()) {
                is Token.NumberLit -> {
                    advance(); token.value
                }
                is Token.StringLit -> {
                    advance(); token.value
                }
                is Token.Ident -> {
                    advance()
                    if (token.name == "true") true
                    else if (token.name == "false") false
                    else if (token.name == "None" || token.name == "null") null
                    else variables[token.name]
                }
                is Token.Op -> {
                    if (token.symbol == "(") {
                        advance()
                        val value = parseOr()
                        if (peek() is Token.Op && (peek() as Token.Op).symbol == ")") advance()
                        value
                    } else if (token.symbol == "-") {
                        advance()
                        val value = parseFactor()
                        if (value == null) null else -toNum(value)
                    } else {
                        throw ExpressionException("Unexpected token: ${token.symbol}")
                    }
                }
                Token.End -> throw ExpressionException("Unexpected end of expression")
            }
        }

        private fun toBool(v: Any?): Boolean = when (v) {
            null -> false
            is Boolean -> v
            is Double -> v != 0.0
            is String -> v.isNotEmpty()
            else -> true
        }

        private fun toNum(v: Any?): Double = when (v) {
            is Double -> v
            is String -> v.toDoubleOrNull() ?: 0.0
            is Boolean -> if (v) 1.0 else 0.0
            else -> 0.0
        }

        private fun compare(left: Any?, op: String, right: Any?): Boolean {
            // Matches the backend's expression evaluator exactly: ANY
            // comparison (including == and !=) against an unanswered
            // (null) question evaluates to false, never true. Keeping this
            // identical to app/services/expressions.py on the server avoids
            // a question appearing relevant on-device but then failing
            // re-validation once synced.
            if (left == null || right == null) return false
            val bothNumeric = (left is Double || left is Boolean) && (right is Double || right is Boolean)
            return if (bothNumeric) {
                val cmp = toNum(left).compareTo(toNum(right))
                when (op) {
                    "==" -> cmp == 0
                    "!=" -> cmp != 0
                    ">" -> cmp > 0
                    "<" -> cmp < 0
                    ">=" -> cmp >= 0
                    "<=" -> cmp <= 0
                    else -> false
                }
            } else {
                val cmp = left.toString().compareTo(right.toString())
                when (op) {
                    "==" -> cmp == 0
                    "!=" -> cmp != 0
                    ">" -> cmp > 0
                    "<" -> cmp < 0
                    ">=" -> cmp >= 0
                    "<=" -> cmp <= 0
                    else -> false
                }
            }
        }
    }
}
