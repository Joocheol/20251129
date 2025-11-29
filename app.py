import ast
import math
from typing import Any, Dict

import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)


ALLOWED_NAMES: Dict[str, Any] = {
    "np": np,
    "exp": np.exp,
    "log": np.log,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "max": np.maximum,
    "min": np.minimum,
    "maximum": np.maximum,
    "minimum": np.minimum,
    "clip": np.clip,
    "pi": math.pi,
    "e": math.e,
}


class SafeExpressionValidator(ast.NodeVisitor):
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.BoolOp,
        ast.Compare,
        ast.Call,
        ast.Name,
        ast.Constant,
        ast.Load,
        ast.IfExp,
    )

    allowed_ops = (
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.And,
        ast.Or,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
    )

    def visit(self, node: ast.AST) -> Any:
        if not isinstance(node, self.allowed_nodes):
            raise ValueError(f"Unsupported expression component: {type(node).__name__}")
        return super().visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_NAMES:
            raise ValueError(f"Function '{getattr(node.func, 'id', None)}' is not allowed.")
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id not in ALLOWED_NAMES and node.id not in {"S_T", "K", "S0", "r"}:
            raise ValueError(f"Variable '{node.id}' is not allowed.")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        if not isinstance(node.op, self.allowed_ops):
            raise ValueError(f"Operator '{type(node.op).__name__}' is not allowed.")
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        if not isinstance(node.op, self.allowed_ops):
            raise ValueError(f"Operator '{type(node.op).__name__}' is not allowed.")
        self.visit(node.operand)

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        if not isinstance(node.op, self.allowed_ops):
            raise ValueError(f"Boolean operator '{type(node.op).__name__}' is not allowed.")
        for value in node.values:
            self.visit(value)

    def visit_Compare(self, node: ast.Compare) -> Any:
        for op in node.ops:
            if not isinstance(op, self.allowed_ops):
                raise ValueError(f"Comparator '{type(op).__name__}' is not allowed.")
        self.visit(node.left)
        for comparator in node.comparators:
            self.visit(comparator)

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)


def safe_eval(expression: str, env: Dict[str, Any]) -> Any:
    parsed = ast.parse(expression, mode="eval")
    SafeExpressionValidator().visit(parsed)
    compiled = compile(parsed, filename="<string>", mode="eval")
    return eval(compiled, {"__builtins__": {}}, env)


def black_scholes_monte_carlo(
    spot_price: float,
    strike_price: float,
    risk_free_rate: float,
    volatility: float,
    maturity: float,
    payoff_expression: str,
    simulations: int = 50000,
) -> float:
    if maturity <= 0:
        raise ValueError("Maturity must be positive.")
    if volatility <= 0:
        raise ValueError("Volatility must be positive.")
    if simulations <= 0:
        raise ValueError("Number of simulations must be positive.")

    rng = np.random.default_rng()
    drift = (risk_free_rate - 0.5 * volatility**2) * maturity
    shocks = volatility * math.sqrt(maturity) * rng.standard_normal(simulations)
    terminal_prices = spot_price * np.exp(drift + shocks)

    env = {**ALLOWED_NAMES, "S_T": terminal_prices, "K": strike_price, "S0": spot_price, "r": risk_free_rate}
    payoffs = np.asarray(safe_eval(payoff_expression, env), dtype=float)
    expected_payoff = payoffs.mean()
    return math.exp(-risk_free_rate * maturity) * expected_payoff


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    errors = None
    defaults = {
        "spot_price": 100.0,
        "strike_price": 100.0,
        "risk_free_rate": 0.03,
        "volatility": 0.2,
        "maturity": 1.0,
        "simulations": 50000,
        "payoff_expression": "maximum(S_T - K, 0)",
    }

    if request.method == "POST":
        try:
            form_values = {
                "spot_price": request.form.get("spot_price", defaults["spot_price"]),
                "strike_price": request.form.get("strike_price", defaults["strike_price"]),
                "risk_free_rate": request.form.get("risk_free_rate", defaults["risk_free_rate"]),
                "volatility": request.form.get("volatility", defaults["volatility"]),
                "maturity": request.form.get("maturity", defaults["maturity"]),
                "simulations": request.form.get("simulations", defaults["simulations"]),
                "payoff_expression": request.form.get("payoff_expression", defaults["payoff_expression"]),
            }
            spot_price = float(form_values["spot_price"])
            strike_price = float(form_values["strike_price"])
            risk_free_rate = float(form_values["risk_free_rate"])
            volatility = float(form_values["volatility"])
            maturity = float(form_values["maturity"])
            simulations = int(form_values["simulations"])
            payoff_expression = form_values["payoff_expression"].strip()

            defaults.update(
                {
                    "spot_price": spot_price,
                    "strike_price": strike_price,
                    "risk_free_rate": risk_free_rate,
                    "volatility": volatility,
                    "maturity": maturity,
                    "simulations": simulations,
                    "payoff_expression": payoff_expression,
                }
            )

            price = black_scholes_monte_carlo(
                spot_price=spot_price,
                strike_price=strike_price,
                risk_free_rate=risk_free_rate,
                volatility=volatility,
                maturity=maturity,
                payoff_expression=payoff_expression,
                simulations=simulations,
            )
            result = {
                "price": price,
                "inputs": {
                    "spot_price": spot_price,
                    "strike_price": strike_price,
                    "risk_free_rate": risk_free_rate,
                    "volatility": volatility,
                    "maturity": maturity,
                    "simulations": simulations,
                    "payoff_expression": payoff_expression,
                },
            }
        except Exception as exc:
            errors = str(exc)

    return render_template("index.html", result=result, errors=errors, defaults=defaults)


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    app.run(debug=True)
