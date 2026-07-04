(function() {
  const React = window.__HERMES_PLUGIN_SDK__.React;
  const { useState, useEffect, useCallback } = window.__HERMES_PLUGIN_SDK__.hooks;
  const { Card, CardHeader, CardTitle, CardContent, Badge, Button, Input, Label, Select, SelectOption, Separator } = window.__HERMES_PLUGIN_SDK__.components;
  const { cn } = window.__HERMES_PLUGIN_SDK__.utils;
  const fetchJSON = window.__HERMES_PLUGIN_SDK__.fetchJSON;
  
  const e = React.createElement;

  function LiteLLMBudgetPlugin() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [updatingToken, setUpdatingToken] = useState(null);
    const [tempBudgets, setTempBudgets] = useState({});
    const [tempDurations, setTempDurations] = useState({});

    const loadKeys = useCallback(() => {
      setLoading(true);
      fetchJSON("/api/plugins/litellm-budget/keys")
        .then((res) => {
          setData(res);
          setError(null);
          // Initialize temp values
          const budgets = {};
          const durations = {};
          res.keys.forEach((k) => {
            budgets[k.token] = k.max_budget !== null ? String(k.max_budget) : "";
            durations[k.token] = k.budget_duration || "lifetime";
          });
          setTempBudgets(budgets);
          setTempDurations(durations);
        })
        .catch((err) => {
          setError(err.message || "Failed to load keys");
        })
        .finally(() => {
          setLoading(false);
        });
    }, []);

    useEffect(() => {
      loadKeys();
    }, [loadKeys]);

    const handleUpdate = (token) => {
      const budgetStr = tempBudgets[token];
      const maxBudget = budgetStr === "" ? null : parseFloat(budgetStr);
      
      if (budgetStr !== "" && isNaN(maxBudget)) {
        alert("Please enter a valid number for the budget limit.");
        return;
      }

      let duration = tempDurations[token];
      if (duration === "lifetime") {
        duration = null;
      }

      setUpdatingToken(token);
      fetchJSON("/api/plugins/litellm-budget/update-budget", {
        method: "POST",
        body: JSON.stringify({
          token: token,
          max_budget: maxBudget,
          budget_duration: duration
        })
      })
        .then(() => {
          loadKeys();
        })
        .catch((err) => {
          alert("Failed to update budget: " + (err.message || err));
        })
        .finally(() => {
          setUpdatingToken(null);
        });
    };

    if (loading && !data) {
      return e("div", { className: "flex items-center justify-center py-24 text-muted-foreground" }, "Loading LiteLLM Budget Dashboard...");
    }

    if (error) {
      return e("div", { className: "p-6 max-w-4xl mx-auto flex flex-col gap-4" },
        e("div", { className: "p-4 border border-destructive bg-destructive/10 text-destructive rounded-lg" },
          e("h3", { className: "font-semibold mb-1" }, "Error Loading Dashboard"),
          e("p", {}, error)
        ),
        e(Button, { onClick: loadKeys, className: "w-max" }, "Retry")
      );
    }

    const { keys, scope } = data;

    return e("div", { className: "p-6 max-w-5xl mx-auto flex flex-col gap-6" },
      // Title Section
      e("div", { className: "flex items-center justify-between border-b border-border pb-4" },
        e("div", { className: "flex items-center gap-3" },
          // SVG Wallet Icon
          e("svg", {
            className: "w-8 h-8 text-primary",
            fill: "none",
            viewBox: "0 0 24 24",
            stroke: "currentColor",
            strokeWidth: 2
          },
            e("path", { strokeLinecap: "round", strokeLinejoin: "round", d: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" })
          ),
          e("div", {},
            e("h1", { className: "text-2xl font-bold tracking-tight text-foreground font-mondwest" }, "LiteLLM Budgets & Spend"),
            e("p", { className: "text-sm text-muted-foreground" },
              scope === "self" ? "Manage and monitor your personal API key budget" : "Admin Dashboard: Manage budgets for Tim and Chrisann"
            )
          )
        ),
        e(Button, { onClick: loadKeys, size: "sm", ghost: true, className: "text-muted-foreground hover:text-foreground" }, "Refresh")
      ),

      // Keys Grid
      e("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-6" },
        keys.map((k) => {
          const isBlocked = k.blocked === true || (k.max_budget !== null && k.spend >= k.max_budget);
          const percentUsed = k.max_budget ? Math.min(100, Math.max(0, (k.spend / k.max_budget) * 100)) : 0;
          
          return e(Card, { key: k.token, className: cn("litellm-budget-card relative overflow-hidden border border-border bg-card shadow-lg", isBlocked && "border-destructive/30") },
            // Top Accent Line
            e("div", {
              className: cn("absolute top-0 left-0 right-0 h-1", isBlocked ? "bg-destructive" : percentUsed > 80 ? "bg-warning" : "bg-primary")
            }),
            
            e(CardHeader, { className: "pb-4 pt-6" },
              e("div", { className: "flex items-center justify-between" },
                e("div", { className: "flex flex-col" },
                  e("span", { className: "text-lg font-bold text-foreground font-mondwest tracking-wide" }, k.key_alias || "unnamed-key"),
                  e("span", { className: "text-xs font-mono text-muted-foreground" }, k.key_name || "sk-...")
                ),
                e(Badge, { tone: isBlocked ? "destructive" : "success" },
                  isBlocked ? "Blocked / Limit Exceeded" : "Active"
                )
              )
            ),

            e(CardContent, { className: "flex flex-col gap-6" },
              // Spend and Budget numbers
              e("div", { className: "grid grid-cols-2 gap-4 bg-background/30 p-4 border border-border rounded-lg" },
                e("div", { className: "flex flex-col" },
                  e("span", { className: "text-xs text-muted-foreground font-medium uppercase tracking-wider" }, "Current Spend"),
                  e("span", { className: "text-xl font-bold font-mono text-foreground" }, `$${k.spend.toFixed(4)}`)
                ),
                e("div", { className: "flex flex-col" },
                  e("span", { className: "text-xs text-muted-foreground font-medium uppercase tracking-wider" }, "Budget Limit"),
                  e("span", { className: "text-xl font-bold font-mono text-foreground" },
                    k.max_budget !== null ? `$${k.max_budget.toFixed(2)}` : "Unlimited"
                  )
                )
              ),

              // Progress Bar (if budget is set)
              k.max_budget !== null && e("div", { className: "flex flex-col gap-1.5" },
                e("div", { className: "flex justify-between text-xs font-mono" },
                  e("span", { className: "text-muted-foreground" }, "Budget Usage"),
                  e("span", { className: cn("font-bold", percentUsed > 90 ? "text-destructive" : percentUsed > 75 ? "text-warning" : "text-primary") },
                    `${percentUsed.toFixed(1)}%`
                  )
                ),
                e("div", { className: "h-2 w-full bg-muted rounded-full overflow-hidden" },
                  e("div", {
                    className: cn("h-full rounded-full transition-all duration-500", isBlocked ? "bg-destructive" : percentUsed > 80 ? "bg-warning" : "bg-primary"),
                    style: { width: `${percentUsed}%` }
                  })
                )
              ),

              // Reset Interval Info
              e("div", { className: "flex items-center justify-between text-xs text-muted-foreground border-t border-border pt-4" },
                e("span", {}, "Reset Interval:"),
                e("span", { className: "font-semibold text-foreground capitalize" },
                  k.budget_duration ? `${k.budget_duration}ly` : "Lifetime (Never)"
                )
              ),

              // Model Spend Breakdown (if any spend exists)
              k.model_spend && Object.keys(k.model_spend).length > 0 && e("div", { className: "flex flex-col gap-2" },
                e("span", { className: "text-xs text-muted-foreground font-medium uppercase tracking-wider" }, "Model Spend Breakdown"),
                e("div", { className: "model-spend-list max-h-32 overflow-y-auto flex flex-col gap-1.5 pr-1 font-mono text-xs" },
                  Object.entries(k.model_spend).map(([modelName, cost]) => 
                    e("div", { key: modelName, className: "flex justify-between items-center py-1 border-b border-border/30 last:border-0" },
                      e("span", { className: "text-muted-foreground truncate max-w-[70%]" }, modelName),
                      e("span", { className: "text-foreground font-semibold" }, `$${cost.toFixed(4)}`)
                    )
                  )
                )
              ),

              // Separator
              e(Separator, { className: "my-1" }),

              // Budget Adjustment Form
              e("div", { className: "flex flex-col gap-4 bg-background/20 p-4 border border-border/50 rounded-lg" },
                e("h4", { className: "text-xs text-foreground font-bold uppercase tracking-wider" }, "Adjust Budget Limits"),
                
                e("div", { className: "grid grid-cols-2 gap-4" },
                  // Limit Input
                  e("div", { className: "flex flex-col gap-1.5" },
                    e(Label, { htmlFor: `budget-${k.token}`, className: "text-xs text-muted-foreground" }, "Max Budget ($)"),
                    e(Input, {
                      id: `budget-${k.token}`,
                      type: "text",
                      placeholder: "e.g. 10.00",
                      value: tempBudgets[k.token] !== undefined ? tempBudgets[k.token] : "",
                      onChange: (e) => setTempBudgets({ ...tempBudgets, [k.token]: e.target.value }),
                      className: "font-mono"
                    })
                  ),
                  // Reset Select
                  e("div", { className: "flex flex-col gap-1.5" },
                    e(Label, { htmlFor: `duration-${k.token}`, className: "text-xs text-muted-foreground" }, "Reset Interval"),
                    e(Select, {
                      id: `duration-${k.token}`,
                      value: tempDurations[k.token] || "lifetime",
                      onValueChange: (val) => setTempDurations({ ...tempDurations, [k.token]: val })
                    },
                      e(SelectOption, { value: "lifetime" }, "Lifetime (No Reset)"),
                      e(SelectOption, { value: "daily" }, "Daily"),
                      e(SelectOption, { value: "weekly" }, "Weekly"),
                      e(SelectOption, { value: "monthly" }, "Monthly")
                    )
                  )
                ),

                e(Button, {
                  size: "sm",
                  onClick: () => handleUpdate(k.token),
                  disabled: updatingToken === k.token,
                  className: "w-full uppercase mt-2"
                },
                  updatingToken === k.token ? "Saving Limits..." : "Apply Budget Limits"
                )
              )
            )
          );
        })
      )
    );
  }

  // Register the plugin view component
  window.__HERMES_PLUGINS__.register("litellm-budget", LiteLLMBudgetPlugin);
})();
