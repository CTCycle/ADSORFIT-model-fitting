from __future__ import annotations

import gradio as gr

from ADSORFIT.app.client.controllers import (
    get_parameter_defaults,
    load_dataset,
    start_fitting,
)


#-------------------------------------------------------------------------------
def create_interface() -> gr.Blocks:
    parameter_defaults = get_parameter_defaults()
    with gr.Blocks(
        title="ADSORFIT Model Fitting",
        analytics_enabled=False,
        theme="soft",
    ) as demo:
        dataset_state = gr.State(value=None)
        gr.Markdown("## ADSORFIT Model Fitting")

        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                max_iterations = gr.Number(
                    label="Max iteration",
                    minimum=1,
                    maximum=1_000_000,
                    value=1000,
                    precision=0,
                )
                save_best_checkbox = gr.Checkbox(
                    label="Save best fitting data",
                    value=True,
                )
                load_button = gr.UploadButton(
                    "Load dataset",
                    file_types=[".csv", ".xlsx"],
                    file_count="single",
                )
                dataset_stats = gr.Textbox(
                    label="Dataset statistics",
                    lines=12,
                    interactive=False,
                    value="No dataset loaded.",
                )
                start_button = gr.Button(
                    "Start fitting",
                    variant="primary",
                )
                fitting_status = gr.Textbox(
                    label="Fitting status",
                    lines=8,
                    interactive=False,
                )

            with gr.Column(scale=1):
                parameter_metadata: list[tuple[str, str, str]] = []
                parameter_inputs: list[gr.Number] = []
                for model_name, parameters in parameter_defaults.items():
                    with gr.Accordion(model_name, open=False):
                        for parameter_name, (min_default, max_default) in parameters.items():
                            with gr.Row():
                                min_input = gr.Number(
                                    label=f"{parameter_name} min",
                                    value=min_default,
                                    precision=4,
                                )
                                max_input = gr.Number(
                                    label=f"{parameter_name} max",
                                    value=max_default,
                                    precision=4,
                                )
                            parameter_metadata.append((model_name, parameter_name, "min"))
                            parameter_inputs.append(min_input)
                            parameter_metadata.append((model_name, parameter_name, "max"))
                            parameter_inputs.append(max_input)

        parameter_metadata_state = gr.State(parameter_metadata)

        load_button.upload(
            fn=load_dataset,
            inputs=load_button,
            outputs=[dataset_state, dataset_stats],
        )

        start_button.click(
            fn=start_fitting,
            inputs=[
                parameter_metadata_state,
                max_iterations,
                save_best_checkbox,
                dataset_state,
                *parameter_inputs,
            ],
            outputs=fitting_status,
        )

    return demo
