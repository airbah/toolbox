import flet as ft
import os
import threading
from typing import List, Dict
from utils.styles import ColorPalette, TextStyles
from utils.invoice_detector import InvoiceDetector, InvoiceResult
from utils.settings_manager import settings


class InvoiceSorterView(ft.Container):
    """View for scanning, detecting and sorting invoices from Downloads folder."""
    
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.detector = InvoiceDetector()
        self.scan_results: List[InvoiceResult] = []
        self.selected_invoices: Dict[str, bool] = {}  # file_path -> selected
        self.settings_visible = False
        
        # UI Components
        self.status_text = ft.Text("", style=TextStyles.CAPTION)
        self.progress_bar = ft.ProgressBar(visible=False, color=ColorPalette.PRIMARY)
        
        # Settings panel components
        self.company_input = ft.TextField(
            label="Ajouter une société",
            hint_text="Ex: Amazon, OVH, Netflix...",
            border_color=ColorPalette.BORDER,
            focused_border_color=ColorPalette.PRIMARY,
            expand=True,
            on_submit=self._add_company,
        )
        self.companies_list = ft.ListView(spacing=5, height=200)
        self._refresh_companies_list()
        
        # Stats
        self.stats_row = ft.Row([
            self._create_stat_card("📁", "0", "Fichiers scannés", ref_name="scanned"),
            self._create_stat_card("📄", "0", "Factures détectées", ref_name="invoices"),
            self._create_stat_card("🏢", "0", "Sociétés", ref_name="companies"),
        ], spacing=15)
        
        # Scan button
        self.scan_btn = ft.ElevatedButton(
            "Scanner Téléchargements",
            icon=ft.Icons.SEARCH,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.PRIMARY,
                color=ColorPalette.BACKGROUND,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            on_click=self.start_scan,
        )
        
        # Sort button
        self.sort_btn = ft.ElevatedButton(
            "Trier les factures sélectionnées",
            icon=ft.Icons.DRIVE_FILE_MOVE,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.SECONDARY,
                color=ColorPalette.BACKGROUND,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            on_click=self.sort_invoices,
            disabled=True
        )
        
        # Select all checkbox
        self.select_all_checkbox = ft.Checkbox(
            label="Tout sélectionner",
            value=False,
            on_change=self.toggle_select_all,
            active_color=ColorPalette.PRIMARY,
        )
        
        # Settings toggle button
        self.settings_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color=ColorPalette.TEXT_SECONDARY,
            tooltip="Gérer les sociétés",
            on_click=self._toggle_settings,
        )
        
        # Settings panel (collapsible)
        self.settings_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.BUSINESS, color=ColorPalette.PRIMARY),
                    ft.Text("Sociétés prédéfinies", style=TextStyles.SUBHEADER),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=ColorPalette.TEXT_SECONDARY,
                        tooltip="Fermer",
                        on_click=self._toggle_settings,
                    ),
                ]),
                ft.Text(
                    "Ces sociétés seront recherchées en priorité dans les factures.",
                    style=TextStyles.CAPTION,
                ),
                ft.Container(height=10),
                ft.Row([
                    self.company_input,
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE,
                        icon_color=ColorPalette.PRIMARY,
                        tooltip="Ajouter",
                        on_click=self._add_company,
                    ),
                ]),
                ft.Container(height=10),
                ft.Container(
                    content=self.companies_list,
                    bgcolor=ColorPalette.BACKGROUND,
                    border_radius=8,
                    padding=10,
                ),
            ]),
            bgcolor=ColorPalette.SURFACE,
            border_radius=10,
            padding=15,
            visible=False,
            border=ft.border.all(1, ColorPalette.BORDER),
        )
        
        # Results list
        self.results_list = ft.ListView(expand=True, spacing=8)
        
        # Downloads path info
        downloads_path = self.detector.get_downloads_folder()
        invoices_path = self.detector.get_invoices_folder()
        
        # Build the layout
        self.padding = 20
        self.content = ft.Column(
            [
                # Header
                ft.Row([
                    ft.Column([
                        ft.Text("Tri Automatique de Factures", style=TextStyles.HEADER),
                        ft.Text(f"Source: {downloads_path}", style=TextStyles.CAPTION),
                        ft.Text(f"Destination: {invoices_path}", style=TextStyles.CAPTION),
                    ], expand=True),
                    self.settings_btn,
                    self.scan_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=15),
                
                # Settings panel (hidden by default)
                self.settings_panel,
                
                # Stats cards
                self.stats_row,
                
                ft.Container(height=15),
                
                # Progress
                self.progress_bar,
                self.status_text,
                
                ft.Divider(color=ColorPalette.BORDER),
                
                # Actions row
                ft.Row([
                    self.select_all_checkbox,
                    ft.Container(expand=True),
                    self.sort_btn,
                ]),
                
                ft.Container(height=10),
                
                # Results list
                ft.Container(
                    content=self.results_list,
                    expand=True,
                    bgcolor=ColorPalette.CONTAINER_BG,
                    border_radius=10,
                    padding=10,
                ),
            ],
            expand=True,
        )
        
        # References for stat cards
        self.stat_refs = {}
    
    def _create_stat_card(self, icon: str, value: str, label: str, ref_name: str) -> ft.Container:
        """Create a stat card widget."""
        value_text = ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=ColorPalette.PRIMARY)
        self.stat_refs = getattr(self, 'stat_refs', {})
        self.stat_refs[ref_name] = value_text
        
        return ft.Container(
            content=ft.Column([
                ft.Text(icon, size=24),
                value_text,
                ft.Text(label, style=TextStyles.CAPTION),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=ColorPalette.SURFACE,
            border_radius=10,
            padding=15,
            expand=True,
            alignment=ft.alignment.center,
        )
    
    def _update_stats(self, scanned: int = 0, invoices: int = 0, companies: int = 0):
        """Update stat card values."""
        if 'scanned' in self.stat_refs:
            self.stat_refs['scanned'].value = str(scanned)
        if 'invoices' in self.stat_refs:
            self.stat_refs['invoices'].value = str(invoices)
        if 'companies' in self.stat_refs:
            self.stat_refs['companies'].value = str(companies)
    
    def _toggle_settings(self, e=None):
        """Toggle settings panel visibility."""
        self.settings_visible = not self.settings_visible
        self.settings_panel.visible = self.settings_visible
        self.settings_btn.icon_color = ColorPalette.PRIMARY if self.settings_visible else ColorPalette.TEXT_SECONDARY
        self.update()
    
    def _refresh_companies_list(self):
        """Refresh the companies list UI."""
        self.companies_list.controls.clear()
        companies = settings.get_invoice_companies()
        
        if not companies:
            self.companies_list.controls.append(
                ft.Text("Aucune société définie", style=TextStyles.CAPTION, italic=True)
            )
        else:
            for company in companies:
                self.companies_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.BUSINESS, size=16, color=ColorPalette.SECONDARY),
                            ft.Text(company, style=TextStyles.BODY, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=18,
                                icon_color=ColorPalette.ERROR,
                                tooltip="Supprimer",
                                on_click=lambda e, c=company: self._remove_company(c),
                            ),
                        ], spacing=10),
                        bgcolor=ColorPalette.CONTAINER_BG,
                        border_radius=5,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    )
                )
    
    def _add_company(self, e=None):
        """Add a company to the predefined list."""
        company = self.company_input.value.strip()
        if company:
            if settings.add_invoice_company(company):
                self.company_input.value = ""
                self._refresh_companies_list()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"'{company}' ajoutée à la liste"),
                    bgcolor=ColorPalette.SURFACE,
                )
                self.page.snack_bar.open = True
                self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"'{company}' existe déjà"),
                    bgcolor=ColorPalette.ERROR,
                )
                self.page.snack_bar.open = True
                self.page.update()
        self.update()
    
    def _remove_company(self, company: str):
        """Remove a company from the predefined list."""
        if settings.remove_invoice_company(company):
            self._refresh_companies_list()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"'{company}' supprimée de la liste"),
                bgcolor=ColorPalette.SURFACE,
            )
            self.page.snack_bar.open = True
            self.page.update()
        self.update()
    
    def start_scan(self, e):
        """Start scanning the Downloads folder."""
        self.scan_btn.disabled = True
        self.sort_btn.disabled = True
        self.progress_bar.visible = True
        self.status_text.value = "Recherche des fichiers..."
        self.results_list.controls.clear()
        self.scan_results.clear()
        self.selected_invoices.clear()
        self.update()
        
        # Start scanning in background thread
        threading.Thread(target=self._scan_files, daemon=True).start()
    
    def _scan_files(self):
        """Background task to scan files."""
        try:
            # Get list of files
            files = self.detector.scan_downloads_folder()
            total_files = len(files)
            
            if total_files == 0:
                self._update_ui_safe(lambda: self._show_message("Aucun fichier trouvé dans Téléchargements"))
                return
            
            invoices_found = 0
            companies = set()
            
            for i, file_path in enumerate(files):
                # Update progress
                progress = (i + 1) / total_files
                file_name = os.path.basename(file_path)
                self._update_ui_safe(lambda p=progress, f=file_name: self._update_progress(p, f"Analyse: {f}"))
                
                # Analyze file
                result = self.detector.analyze_file(file_path)
                self.scan_results.append(result)
                
                if result.is_invoice:
                    invoices_found += 1
                    self.selected_invoices[result.file_path] = True
                    if result.company_name:
                        companies.add(result.company_name)
                    
                    # Add to UI immediately
                    self._update_ui_safe(lambda r=result: self._add_result_item(r))
                
                # Update stats
                self._update_ui_safe(lambda s=i+1, inv=invoices_found, c=len(companies): self._update_stats(s, inv, c))
            
            # Finish
            self._update_ui_safe(lambda: self._finish_scan(total_files, invoices_found))
            
        except Exception as ex:
            self._update_ui_safe(lambda: self._show_error(str(ex)))
    
    def _update_ui_safe(self, func):
        """Safely update UI from background thread."""
        try:
            func()
            self.update()
        except Exception:
            pass
    
    def _update_progress(self, progress: float, text: str):
        """Update progress bar and status text."""
        self.progress_bar.value = progress
        self.status_text.value = text
    
    def _show_message(self, message: str):
        """Show a message in status."""
        self.status_text.value = message
        self.progress_bar.visible = False
        self.scan_btn.disabled = False
    
    def _show_error(self, error: str):
        """Show an error message."""
        self.status_text.value = f"❌ Erreur: {error}"
        self.progress_bar.visible = False
        self.scan_btn.disabled = False
    
    def _finish_scan(self, total: int, invoices: int):
        """Finish the scan and update UI."""
        self.progress_bar.visible = False
        self.scan_btn.disabled = False
        self.sort_btn.disabled = invoices == 0
        
        if invoices > 0:
            self.status_text.value = f"✅ Scan terminé: {invoices} factures trouvées sur {total} fichiers"
            self.select_all_checkbox.value = True
        else:
            self.status_text.value = f"Scan terminé: aucune facture détectée sur {total} fichiers"
    
    def _add_result_item(self, result: InvoiceResult):
        """Add a result item to the list."""
        item = self._create_result_item(result)
        self.results_list.controls.append(item)
    
    def _create_result_item(self, result: InvoiceResult) -> ft.Container:
        """Create a visual item for an invoice result."""
        # Confidence indicator
        confidence_color = ColorPalette.PRIMARY if result.confidence_score > 0.6 else ColorPalette.SECONDARY
        confidence_text = f"{int(result.confidence_score * 100)}%"
        
        # Company name field (editable)
        company_field = ft.TextField(
            value=result.company_name or "Inconnu",
            label="Société",
            border_color=ColorPalette.BORDER,
            focused_border_color=ColorPalette.PRIMARY,
            text_style=TextStyles.BODY,
            width=200,
            height=45,
            content_padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            on_change=lambda e, r=result: self._update_company_name(r, e.control.value),
        )
        
        # Checkbox for selection
        checkbox = ft.Checkbox(
            value=self.selected_invoices.get(result.file_path, True),
            on_change=lambda e, r=result: self._toggle_selection(r, e.control.value),
            active_color=ColorPalette.PRIMARY,
        )
        
        # Keywords preview
        keywords_text = ", ".join(result.detected_keywords[:5])
        if len(result.detected_keywords) > 5:
            keywords_text += f" (+{len(result.detected_keywords) - 5})"
        
        return ft.Container(
            content=ft.Row([
                checkbox,
                ft.Icon(
                    ft.Icons.PICTURE_AS_PDF if result.file_path.lower().endswith('.pdf') else ft.Icons.IMAGE,
                    size=32,
                    color=ColorPalette.SECONDARY
                ),
                ft.Column([
                    ft.Text(result.file_name, style=TextStyles.BODY, weight=ft.FontWeight.BOLD, max_lines=1),
                    ft.Text(f"Mots-clés: {keywords_text}", style=TextStyles.CAPTION, max_lines=1),
                ], expand=True, spacing=2),
                ft.Container(
                    content=ft.Text(confidence_text, size=12, weight=ft.FontWeight.BOLD, color=ColorPalette.BACKGROUND),
                    bgcolor=confidence_color,
                    border_radius=5,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.Icon(ft.Icons.ARROW_FORWARD, color=ColorPalette.TEXT_SECONDARY, size=20),
                company_field,
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            bgcolor=ColorPalette.SURFACE,
            border_radius=8,
            padding=12,
        )
    
    def _update_company_name(self, result: InvoiceResult, new_name: str):
        """Update the company name for a result."""
        result.company_name = new_name
    
    def _toggle_selection(self, result: InvoiceResult, selected: bool):
        """Toggle selection for a result."""
        self.selected_invoices[result.file_path] = selected
        
        # Update select all checkbox
        all_selected = all(self.selected_invoices.values())
        self.select_all_checkbox.value = all_selected
        self.select_all_checkbox.update()
        
        # Update sort button
        any_selected = any(self.selected_invoices.values())
        self.sort_btn.disabled = not any_selected
        self.sort_btn.update()
    
    def toggle_select_all(self, e):
        """Toggle selection for all items."""
        select_all = e.control.value
        
        for result in self.scan_results:
            if result.is_invoice:
                self.selected_invoices[result.file_path] = select_all
        
        # Update sort button
        self.sort_btn.disabled = not select_all or len(self.selected_invoices) == 0
        
        # Rebuild the list to update checkboxes
        self._rebuild_results_list()
        self.update()
    
    def _rebuild_results_list(self):
        """Rebuild the results list with current data."""
        self.results_list.controls.clear()
        for result in self.scan_results:
            if result.is_invoice:
                self.results_list.controls.append(self._create_result_item(result))
    
    def sort_invoices(self, e):
        """Move selected invoices to their destination folders."""
        self.sort_btn.disabled = True
        self.scan_btn.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = None  # Indeterminate
        self.status_text.value = "Déplacement des factures..."
        self.update()
        
        # Run in background
        threading.Thread(target=self._move_invoices, daemon=True).start()
    
    def _move_invoices(self):
        """Background task to move invoices."""
        moved_count = 0
        error_count = 0
        
        selected_results = [r for r in self.scan_results 
                          if r.is_invoice and self.selected_invoices.get(r.file_path, False)]
        
        total = len(selected_results)
        
        for i, result in enumerate(selected_results):
            company = self.detector.normalize_company_name(result.company_name)
            success, message = self.detector.move_invoice(result.file_path, company)
            
            if success:
                moved_count += 1
                # Remove from list
                self.selected_invoices.pop(result.file_path, None)
            else:
                error_count += 1
                print(f"Error moving {result.file_name}: {message}")
            
            progress = (i + 1) / total
            self._update_ui_safe(lambda p=progress: self._update_progress(p, f"Déplacement en cours... {i+1}/{total}"))
        
        # Finish
        self._update_ui_safe(lambda: self._finish_sort(moved_count, error_count))
    
    def _finish_sort(self, moved: int, errors: int):
        """Finish the sort operation."""
        self.progress_bar.visible = False
        self.scan_btn.disabled = False
        
        # Remove moved items from results
        self.scan_results = [r for r in self.scan_results if r.file_path in self.selected_invoices]
        self._rebuild_results_list()
        
        # Update stats
        remaining = len([r for r in self.scan_results if r.is_invoice])
        companies = set(r.company_name for r in self.scan_results if r.is_invoice and r.company_name)
        self._update_stats(len(self.scan_results), remaining, len(companies))
        
        if errors > 0:
            self.status_text.value = f"✅ {moved} factures déplacées, ❌ {errors} erreurs"
        else:
            self.status_text.value = f"✅ {moved} factures déplacées avec succès!"
        
        # Disable sort if no more selected
        self.sort_btn.disabled = remaining == 0
        
        # Show snackbar
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"{moved} factures triées dans le dossier 'factures'"),
            bgcolor=ColorPalette.SURFACE,
        )
        self.page.snack_bar.open = True
        self.page.update()
        
        self.update()

