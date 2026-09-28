// Small, safe evaluator for survey "skip logic" expressions such as
//   gender == 'FEMALE'
//   age >= 18 and age < 65
//   'malaria' in symptoms
// It mirrors the backend/Android evaluators: unanswered questions are null,
// a comparison with null is false, and a broken expression fails open
// (the question stays visible).

type Value = string | number | boolean | null | Value[];
type Token = { t: "num" | "str" | "name" | "op"; v: string };

function tokenize(src: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (/\s/.test(c)) {
      i++;
      continue;
    }
    if (/[0-9]/.test(c) || (c === "." && /[0-9]/.test(src[i + 1] ?? ""))) {
      let j = i + 1;
      while (j < src.length && /[0-9.]/.test(src[j])) j++;
      tokens.push({ t: "num", v: src.slice(i, j) });
      i = j;
      continue;
    }
    if (c === "'" || c === '"') {
      let j = i + 1;
      let out = "";
      while (j < src.length && src[j] !== c) {
        if (src[j] === "\\" && j + 1 < src.length) j++;
        out += src[j];
        j++;
      }
      if (j >= src.length) throw new Error("Unterminated string");
      tokens.push({ t: "str", v: out });
      i = j + 1;
      continue;
    }
    if (/[A-Za-z_]/.test(c)) {
      let j = i + 1;
      while (j < src.length && /[A-Za-z0-9_]/.test(src[j])) j++;
      tokens.push({ t: "name", v: src.slice(i, j) });
      i = j;
      continue;
    }
    const two = src.slice(i, i + 2);
    if (["==", "!=", "<=", ">="].includes(two)) {
      tokens.push({ t: "op", v: two });
      i += 2;
      continue;
    }
    if ("<>+-*/%()[],".includes(c)) {
      tokens.push({ t: "op", v: c });
      i++;
      continue;
    }
    throw new Error(`Unexpected character ${c}`);
  }
  return tokens;
}

function truthy(v: Value | undefined): boolean {
  if (v === null || v === undefined) return false;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "string") return v.length > 0;
  return Boolean(v);
}

class Parser {
  private pos = 0;
  constructor(private tokens: Token[], private vars: Record<string, Value>) {}

  private peek(): Token | undefined {
    return this.tokens[this.pos];
  }
  private isOp(v: string): boolean {
    const t = this.peek();
    return !!t && t.t === "op" && t.v === v;
  }
  private isWord(v: string): boolean {
    const t = this.peek();
    return !!t && t.t === "name" && t.v === v;
  }

  parse(): Value {
    const v = this.orExpr();
    if (this.pos < this.tokens.length) throw new Error("Unexpected trailing input");
    return v;
  }

  private orExpr(): Value {
    let result = truthy(this.andExpr());
    while (this.isWord("or")) {
      this.pos++;
      const right = truthy(this.andExpr());
      result = result || right;
    }
    return result;
  }

  private andExpr(): Value {
    let result = truthy(this.notExpr());
    while (this.isWord("and")) {
      this.pos++;
      const right = truthy(this.notExpr());
      result = result && right;
    }
    return result;
  }

  private notExpr(): Value {
    if (this.isWord("not")) {
      this.pos++;
      return !truthy(this.notExpr());
    }
    return this.comparison();
  }

  private compareOp(): string | null {
    const t = this.peek();
    if (!t) return null;
    if (t.t === "op" && ["==", "!=", "<", "<=", ">", ">="].includes(t.v)) {
      this.pos++;
      return t.v;
    }
    if (t.t === "name" && t.v === "in") {
      this.pos++;
      return "in";
    }
    if (t.t === "name" && t.v === "not" && this.tokens[this.pos + 1]?.t === "name" && this.tokens[this.pos + 1]?.v === "in") {
      this.pos += 2;
      return "not in";
    }
    return null;
  }

  private comparison(): Value {
    let left = this.arith();
    let sawOp = false;
    let ok = true;
    for (;;) {
      const op = this.compareOp();
      if (!op) break;
      sawOp = true;
      const right = this.arith();
      if (ok) {
        if (left === null || right === null) {
          ok = false;
        } else {
          ok = applyCompare(op, left, right);
        }
      }
      left = right;
    }
    return sawOp ? ok : left;
  }

  private arith(): Value {
    let left = this.term();
    while (this.isOp("+") || this.isOp("-")) {
      const op = this.peek()!.v;
      this.pos++;
      const right = this.term();
      left = binop(op, left, right);
    }
    return left;
  }

  private term(): Value {
    let left = this.unary();
    while (this.isOp("*") || this.isOp("/") || this.isOp("%")) {
      const op = this.peek()!.v;
      this.pos++;
      const right = this.unary();
      left = binop(op, left, right);
    }
    return left;
  }

  private unary(): Value {
    if (this.isOp("-")) {
      this.pos++;
      const v = this.unary();
      return typeof v === "number" ? -v : null;
    }
    return this.primary();
  }

  private primary(): Value {
    const t = this.peek();
    if (!t) throw new Error("Unexpected end");
    this.pos++;
    if (t.t === "num") return parseFloat(t.v);
    if (t.t === "str") return t.v;
    if (t.t === "name") {
      if (t.v === "True") return true;
      if (t.v === "False") return false;
      if (t.v === "None") return null;
      return t.v in this.vars ? this.vars[t.v] : null;
    }
    if (t.v === "(") {
      const v = this.orExpr();
      if (!this.isOp(")")) throw new Error("Missing )");
      this.pos++;
      return v;
    }
    if (t.v === "[") {
      const items: Value[] = [];
      if (this.isOp("]")) {
        this.pos++;
        return items;
      }
      for (;;) {
        items.push(this.orExpr());
        if (this.isOp(",")) {
          this.pos++;
          continue;
        }
        if (this.isOp("]")) {
          this.pos++;
          break;
        }
        throw new Error("Bad list");
      }
      return items;
    }
    throw new Error(`Unexpected token ${t.v}`);
  }
}

function binop(op: string, a: Value, b: Value): Value {
  if (a === null || b === null) return null;
  if (typeof a === "number" && typeof b === "number") {
    switch (op) {
      case "+":
        return a + b;
      case "-":
        return a - b;
      case "*":
        return a * b;
      case "/":
        return b === 0 ? null : a / b;
      case "%":
        return b === 0 ? null : a % b;
    }
  }
  if (op === "+" && typeof a === "string" && typeof b === "string") return a + b;
  return null;
}

function applyCompare(op: string, a: Value, b: Value): boolean {
  switch (op) {
    case "==":
      return JSON.stringify(a) === JSON.stringify(b);
    case "!=":
      return JSON.stringify(a) !== JSON.stringify(b);
    case "<":
      return (a as number | string) < (b as number | string);
    case "<=":
      return (a as number | string) <= (b as number | string);
    case ">":
      return (a as number | string) > (b as number | string);
    case ">=":
      return (a as number | string) >= (b as number | string);
    case "in":
      return contains(b, a);
    case "not in":
      return !contains(b, a);
  }
  return false;
}

function contains(container: Value, item: Value): boolean {
  if (Array.isArray(container)) return container.some((x) => JSON.stringify(x) === JSON.stringify(item));
  if (typeof container === "string") return typeof item === "string" && container.includes(item);
  return false;
}

/** Turns typed answers into expression values: numeric text becomes a number. */
export function coerceAnswer(value: string | string[] | undefined): Value {
  if (value === undefined) return null;
  if (Array.isArray(value)) return value;
  if (value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) && value.trim() !== "" ? n : value;
}

export function isRelevant(expression: string | null | undefined, vars: Record<string, Value>): boolean {
  if (!expression || !expression.trim()) return true;
  try {
    return truthy(new Parser(tokenize(expression), vars).parse());
  } catch {
    return true; // a broken expression must never hide a question
  }
}

export type { Value as ExpressionValue };
