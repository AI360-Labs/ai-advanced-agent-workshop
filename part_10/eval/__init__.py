"""Offline evaluation harness for the agent's intent classifier.

``metrics`` holds pure, deterministic metric math (no LLM, no MLflow).
``run_intent_eval`` runs the live classifier over the labelled dataset and
logs the resulting precision / recall / accuracy to MLflow.
"""
