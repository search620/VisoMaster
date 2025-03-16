import json
from pathlib import Path
from PySide6 import QtWidgets
from typing import TYPE_CHECKING
from functools import partial

from app.ui.widgets.actions import common_actions as common_widget_actions
from app.helpers.miscellaneous import ParametersDict

if TYPE_CHECKING:
    from app.ui.main_ui import MainWindow
    from PySide6.QtWidgets import QListWidgetItem

def handle_preset_double_click(main_window: 'MainWindow', item: 'QListWidgetItem'):
    """Handle double click on preset item by showing confirmation dialog"""
    result = QtWidgets.QMessageBox.question(
        main_window,
        'Apply Preset',
        f'Do you want to apply preset: {item.text()}?',
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    )

    if result == QtWidgets.QMessageBox.Yes:
        apply_selected_preset(main_window)

def overwrite_selected_preset(main_window: 'MainWindow'):
    """Overwrite the selected preset with current parameters"""
    current_item = main_window.presetsList.currentItem()
    if not current_item:
        common_widget_actions.create_and_show_messagebox(
            main_window,
            'No Preset Selected',
            'Please select a preset to overwrite',
            parent_widget=main_window
        )
        return

    # Get confirmation
    result = QtWidgets.QMessageBox.question(
        main_window,
        'Confirm Overwrite',
        f'Are you sure you want to overwrite preset: {current_item.text()}?',
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    )

    if result == QtWidgets.QMessageBox.Yes:
        preset_path = Path("presets") / f"{current_item.text()}.json"
        preset_path.parent.mkdir(exist_ok=True)
        
        # Get current parameters but exclude input/output paths
        current_params = {}
        if main_window.selected_target_face_id:
            params = main_window.parameters[main_window.selected_target_face_id].data.copy()
            params.pop('InputFolder', None)
            params.pop('OutputFolder', None)
            current_params = params
        else:
            params = main_window.current_widget_parameters.data.copy()
            params.pop('InputFolder', None)
            params.pop('OutputFolder', None)
            current_params = params

        # Save to file
        with open(preset_path, 'w') as f:
            json.dump(current_params, f, indent=4)

        common_widget_actions.create_and_show_toast_message(
            main_window,
            'Preset Updated',
            f'Overwritten preset: {current_item.text()}'
        )

def refresh_presets_list(main_window: 'MainWindow'):
    """Refresh the presets list with all JSON files in the presets directory"""
    main_window.presetsList.clear()
    presets_dir = Path("presets")
    if not presets_dir.exists():
        presets_dir.mkdir(exist_ok=True)
    
    for json_file in presets_dir.glob("*.json"):
        main_window.presetsList.addItem(json_file.stem)

def save_current_as_preset(main_window: 'MainWindow'):
    """Save current parameters as a preset JSON file"""
    name, ok = QtWidgets.QInputDialog.getText(main_window, "Save Preset", "Enter preset name:")
    if ok and name:
        preset_path = Path("presets") / f"{name}.json"
        preset_path.parent.mkdir(exist_ok=True)
        
        # Get current parameters but exclude input/output paths
        current_params = {}
        if main_window.selected_target_face_id:
            params = main_window.parameters[main_window.selected_target_face_id].data.copy()
            # Remove any input/output specific settings
            params.pop('InputFolder', None)
            params.pop('OutputFolder', None)
            current_params = params
        else:
            params = main_window.current_widget_parameters.data.copy()
            params.pop('InputFolder', None) 
            params.pop('OutputFolder', None)
            current_params = params

        # Save to file
        with open(preset_path, 'w') as f:
            json.dump(current_params, f, indent=4)
        
        refresh_presets_list(main_window)
        common_widget_actions.create_and_show_toast_message(
            main_window, 
            'Preset Saved', 
            f'Saved preset: {name}'
        )

def apply_selected_preset(main_window: 'MainWindow'):
    """Apply the selected preset while preserving input/output directories"""
    current_item = main_window.presetsList.currentItem()
    if not current_item:
        return

    preset_path = Path("presets") / f"{current_item.text()}.json"
    if not preset_path.exists():
        return

    with open(preset_path, 'r') as f:
        preset_params = json.load(f)

    # Preserve current input/output directories
    if main_window.selected_target_face_id:
        current_params = main_window.parameters[main_window.selected_target_face_id]
        input_folder = current_params.get('InputFolder')
        output_folder = current_params.get('OutputFolder')
        
        # Update parameters with preset while preserving paths
        new_params = preset_params.copy()
        if input_folder:
            new_params['InputFolder'] = input_folder
        if output_folder:
            new_params['OutputFolder'] = output_folder
            
        main_window.parameters[main_window.selected_target_face_id] = ParametersDict(new_params, main_window.default_parameters)
        if main_window.selected_target_face_id == main_window.selected_target_face_id:
            common_widget_actions.set_widgets_values_using_face_id_parameters(main_window, main_window.selected_target_face_id)
        else:
            # Handle case when no face is selected
            current_input = main_window.current_widget_parameters.get('InputFolder', '')
            current_output = main_window.current_widget_parameters.get('OutputFolder', '')
            
            new_params = preset_params.copy()
            if current_input:
                new_params['InputFolder'] = current_input
            if current_output:
                new_params['OutputFolder'] = current_output
            
        main_window.current_widget_parameters = ParametersDict(new_params, main_window.default_parameters)
        common_widget_actions.set_widgets_values_using_face_id_parameters(main_window, False)

    # Refresh the frame to show changes
    common_widget_actions.refresh_frame(main_window)
    common_widget_actions.create_and_show_toast_message(
        main_window,
        'Preset Applied',
        f'Applied preset: {current_item.text()}'
    )