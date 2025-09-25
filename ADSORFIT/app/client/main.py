from __future__ import annotations

import gradio as gr

from Pharmagent.app.configurations import ClientRuntimeConfig
from Pharmagent.app.constants import (
    AGENT_MODEL_CHOICES,
    CLOUD_MODEL_CHOICES,
    CLOUD_PROVIDERS,
    PARSING_MODEL_CHOICES,
)
from Pharmagent.app.client.controllers import (
    clear_agent_fields,
    fetch_clinical_data,
    preload_selected_models,
    pull_selected_models,
    run_agent,
    set_agent_model,
    set_cloud_model,
    set_llm_provider,
    set_parsing_model,
    start_ollama_client,
    toggle_cloud_services,
)


###############################################################################
def create_interface() -> gr.Blocks:
    provider = ClientRuntimeConfig.get_llm_provider()
    cloud_models = CLOUD_MODEL_CHOICES.get(provider, [])
    selected_cloud_model = ClientRuntimeConfig.get_cloud_model()
    if selected_cloud_model not in cloud_models:
        selected_cloud_model = cloud_models[0] if cloud_models else ""
        ClientRuntimeConfig.set_cloud_model(selected_cloud_model)
    with gr.Blocks(
        title="Pharmagent Clinical Copilot",
        analytics_enabled=False,
        theme="soft",
    ) as demo:
        gr.Markdown("## Pharmagent Clinical Copilot")

        with gr.Row():
            with gr.Column(scale=3):
                anamnesis = gr.Textbox(
                    label="Anamnesis",
                    placeholder="Enter anamnesis details...",
                    lines=10,
                    max_lines=100,
                )
                has_diseases = gr.Checkbox(
                    label="Has hepatic diseases",
                    value=False,
                )
                symptoms = gr.CheckboxGroup(
                    label="Observed symptoms",
                    choices=["Hitterus", "Pain", "Scretching"],
                )
                drugs = gr.Textbox(
                    label="Current Drugs",
                    placeholder="List current therapies, dosage and schedule...",
                    lines=10,
                    max_lines=100,
                )
                exams = gr.Textbox(
                    label="Additional Exams",
                    placeholder="Provide lab or imaging exam notes...",
                    lines=10,
                    max_lines=100,
                )
                with gr.Row():
                    alt = gr.Textbox(
                        label="ALT",
                        placeholder="e.g., 189 or 189 U/L",
                        lines=1,
                        scale=3,
                    )
                    alt_max = gr.Textbox(
                        label="ALT Max",
                        placeholder="e.g., 47 U/L",
                        lines=1,
                        scale=2,
                    )
                with gr.Row():
                    alp = gr.Textbox(
                        label="ALP",
                        placeholder="e.g., 140 or 140 U/L",
                        lines=1,
                        scale=3,
                    )
                    alp_max = gr.Textbox(
                        label="ALP Max",
                        placeholder="e.g., 150 U/L",
                        lines=1,
                        scale=2,
                    )

            with gr.Column(scale=1):
                patient_name = gr.Textbox(
                    label="Patient Name",
                    placeholder="e.g., Marco Rossi",
                    lines=1,
                )
                process_from_files = gr.Checkbox(
                    label="Process patients from files",
                    value=False,
                )
                translate_to_eng = gr.Checkbox(
                    label="Always translate to English",
                    value=False,
                )
                with gr.Column():
                    run_button = gr.Button("Run Workflow", variant="primary")
                    skip_download_checkbox = gr.Checkbox(
                        label="Skip clinical data download",
                        value=False,
                    )
                    get_clinical_data_button = gr.Button(
                        "Get Clinical Data",
                        variant="secondary",
                    )
                    clear_button = gr.Button("Clear all")
                    ollama_status = gr.Markdown(value="", visible=True)
                with gr.Accordion("Runtime Configuration", open=False):
                    with gr.Column():
                        with gr.Row():
                            with gr.Column(scale=1):
                                use_cloud_services = gr.Checkbox(
                                    label="Use Cloud Services",
                                    value=ClientRuntimeConfig.is_cloud_enabled(),
                                )
                                llm_provider_dropdown = gr.Dropdown(
                                    label="Cloud Service",
                                    choices=CLOUD_PROVIDERS,
                                    value=provider,
                                    interactive=ClientRuntimeConfig.is_cloud_enabled(),
                                )
                            cloud_model_dropdown = gr.Dropdown(
                                label="Cloud Model",
                                choices=cloud_models,
                                value=selected_cloud_model,
                                interactive=ClientRuntimeConfig.is_cloud_enabled(),
                            )
                        with gr.Row():
                            with gr.Column(scale=1):
                                parsing_model_dropdown = gr.Dropdown(
                                    label="Parsing Model",
                                    choices=PARSING_MODEL_CHOICES,
                                    value=ClientRuntimeConfig.get_parsing_model(),
                                )
                                agent_model_dropdown = gr.Dropdown(
                                    label="Agent Model",
                                    choices=AGENT_MODEL_CHOICES,
                                    value=ClientRuntimeConfig.get_agent_model(),
                                )
                                pull_models_button = gr.Button(
                                    "Pull models",
                                    variant="secondary",
                                )
                                start_ollama_button = gr.Button(
                                    "Start Ollama client",
                                    variant="secondary",
                                    interactive=not ClientRuntimeConfig.is_cloud_enabled(),
                                )
                                preload_button = gr.Button(
                                    "Preload models",
                                    variant="secondary",
                                    interactive=not ClientRuntimeConfig.is_cloud_enabled(),
                                )
                            pull_status = gr.Markdown(value="", visible=True)

        output = gr.Textbox(
            label="Agent Output",
            lines=30,
            show_copy_button=True,
            interactive=False,
        )

        use_cloud_services.change(
            fn=toggle_cloud_services,
            inputs=use_cloud_services,
            outputs=[
                llm_provider_dropdown,
                cloud_model_dropdown,
                start_ollama_button,
                preload_button,
            ],
        )
        llm_provider_dropdown.change(
            fn=set_llm_provider,
            inputs=llm_provider_dropdown,
            outputs=[llm_provider_dropdown, cloud_model_dropdown],
        )
        cloud_model_dropdown.change(
            fn=set_cloud_model,
            inputs=cloud_model_dropdown,
            outputs=cloud_model_dropdown,
        )
        parsing_model_dropdown.change(
            fn=set_parsing_model,
            inputs=parsing_model_dropdown,
            outputs=parsing_model_dropdown,
        )
        agent_model_dropdown.change(
            fn=set_agent_model,
            inputs=agent_model_dropdown,
            outputs=agent_model_dropdown,
        )

        pull_models_button.click(
            fn=pull_selected_models,
            inputs=[parsing_model_dropdown, agent_model_dropdown],
            outputs=pull_status,
        )

        run_button.click(
            fn=run_agent,
            inputs=[
                patient_name,
                anamnesis,
                drugs,
                exams,
                alt,
                alt_max,
                alp,
                alp_max,
                symptoms,
                process_from_files,
                translate_to_eng,
            ],
            outputs=output,
            api_name="run_agent",
        )
        start_ollama_button.click(
            fn=start_ollama_client,
            outputs=ollama_status,
        )
        preload_button.click(
            fn=preload_selected_models,
            inputs=[parsing_model_dropdown, agent_model_dropdown],
            outputs=ollama_status,
        )
        get_clinical_data_button.click(
            fn=fetch_clinical_data,
            inputs=skip_download_checkbox,
            outputs=ollama_status,
        )
        clear_button.click(
            fn=clear_agent_fields,
            outputs=[
                patient_name,
                anamnesis,
                drugs,
                exams,
                alt,
                alt_max,
                alp,
                alp_max,
                symptoms,
                process_from_files,
                translate_to_eng,
                skip_download_checkbox,
                has_diseases,
                output,
                ollama_status,
            ],
        )

    return demo


###############################################################################
def launch_interface() -> None:
    create_interface().queue(max_size=32).launch(
        server_name="127.0.0.1",
        server_port=7861,
        inbrowser=True,
    )


if __name__ == "__main__":
    launch_interface()
