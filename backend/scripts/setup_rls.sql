CREATE ROLE quering_agent LOGIN PASSWORD '1234' NOSUPERUSER NOCREATEDB;

GRANT CONNECT ON DATABASE finance TO quering_agent;
GRANT USAGE ON SCHEMA public TO quering_agent;
GRANT SELECT ON transactions, budgets, goals, categories, merchant_data TO quering_agent;

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY agent_user_isolation_transaction ON  transactions 
FOR SELECT TO quering_agent USING (user_id = current_setting('app.user_id',true)::int);

ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
CREATE POLICY agent_user_isolation_budgets ON  budgets 
FOR SELECT TO quering_agent USING (user_id = current_setting('app.user_id',true)::int);

ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
CREATE POLICY agent_user_isolation_goals ON  goals 
FOR SELECT TO quering_agent USING (user_id = current_setting('app.user_id',true)::int);

ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY agent_user_isolation_categories ON  categories 
FOR SELECT TO quering_agent USING (user_id = current_setting('app.user_id', true)::int OR user_id IS NULL);
