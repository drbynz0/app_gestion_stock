from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import InternalOrder, Payment
from .serializers import (
    InternalOrderSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    InternalOrderPaymentSerializer,
)
from users.tenancy import CompanyQuerysetMixin
from users.permissions_company import HasOrderPermission
from historical.utils import log_activity


class InternalOrderListCreateView(CompanyQuerysetMixin, generics.ListCreateAPIView):
    queryset = InternalOrder.objects.all().order_by('-created_at')
    serializer_class = InternalOrderSerializer
    permission_classes = [HasOrderPermission]

    def perform_create(self, serializer):
        order = serializer.save(company=self.request.user.company)
        log_activity(
            self.request.user.company,
            f"Commande client créée : #{order.order_num} – {order.client_name}",
            "clipboard-text-outline",
        )


class InternalOrderDetailView(CompanyQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = InternalOrder.objects.all()
    serializer_class = InternalOrderSerializer
    permission_classes = [HasOrderPermission]


class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [HasOrderPermission]

    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return Payment.objects.filter(order_id=order_id, order__company=self.request.user.company).order_by('-date')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(InternalOrder, pk=order_id, company=self.request.user.company)
        payment = serializer.save(order=order)
        log_activity(
            self.request.user.company,
            f"Règlement enregistré : {payment.amount} sur commande #{order.order_num}",
            "cash-check",
        )


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [HasOrderPermission]

    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return Payment.objects.filter(order_id=order_id, order__company=self.request.user.company)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PaymentCreateSerializer
        return super().get_serializer_class()

    def perform_update(self, serializer):
        payment = self.get_object()
        old_amount = payment.amount
        order = payment.order
        new_amount = serializer.validated_data['amount']
        amount_diff = new_amount - old_amount
        order.total_paid += amount_diff
        order.remaining_price = order.total_price - order.total_paid
        if order.remaining_price <= 0:
            order.status = 'completed'
        else:
            order.status = 'toPay'
        order.save()
        serializer.save()

    def perform_destroy(self, instance):
        order = instance.order
        amount = instance.amount
        order.total_paid -= amount
        order.remaining_price = order.total_price - order.total_paid
        if order.remaining_price > 0:
            order.status = 'toPay'
        order.save()
        instance.delete()


class InternalOrderInvoiceView(APIView):
    """
    GET /api/internal-orders/<pk>/invoice/
    Génère et retourne la facture PDF complète de la commande.
    """
    permission_classes = [HasOrderPermission]

    def get(self, request, pk):
        order = get_object_or_404(InternalOrder, pk=pk, company=request.user.company)
        pdf_bytes = self._generate_pdf(order, request.user.company)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="facture-{order.order_num}.pdf"'
        return response

    def _generate_pdf(self, order, company):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
        import io, urllib.request
        from customers.models import Customer

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.8*cm, bottomMargin=1.8*cm
        )

        PRIMARY = colors.HexColor('#00A86B')
        DARK = colors.HexColor('#0F172A')
        GRAY = colors.HexColor('#64748B')
        LIGHT_BG = colors.HexColor('#F8FAFC')
        BORDER_COLOR = colors.HexColor('#E2E8F0')

        title_style = ParagraphStyle('Title', fontSize=20, textColor=DARK, fontName='Helvetica-Bold', spaceAfter=3)
        invoice_word = ParagraphStyle('InvWord', fontSize=24, textColor=PRIMARY, fontName='Helvetica-Bold', alignment=TA_RIGHT, spaceAfter=5)
        sub_style = ParagraphStyle('Sub', fontSize=8, textColor=GRAY, fontName='Helvetica', spaceAfter=2)
        bold_style = ParagraphStyle('Bold', fontSize=9, textColor=DARK, fontName='Helvetica-Bold', spaceAfter=2)
        normal_style = ParagraphStyle('Normal2', fontSize=8.5, textColor=DARK, fontName='Helvetica', spaceAfter=2)
        right_style = ParagraphStyle('Right', fontSize=8.5, textColor=DARK, fontName='Helvetica', alignment=TA_RIGHT)
        right_bold = ParagraphStyle('RightB', fontSize=9, textColor=DARK, fontName='Helvetica-Bold', alignment=TA_RIGHT)
        header_cell = ParagraphStyle('HCell', fontSize=8.5, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)
        sec_title = ParagraphStyle('SecTitle', fontSize=11, textColor=DARK, fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=4)

        currency = getattr(company, 'currency', 'MAD')

        # Récupération informations client
        client_phone = '-'
        client_email = '-'
        client_address = '-'
        client_ice = None
        try:
            customer = Customer.objects.get(company=company, id=order.client_id)
            if customer.phone_number: client_phone = customer.phone_number
            if customer.email: client_email = customer.email
            if customer.address: client_address = customer.address
            if customer.ice: client_ice = customer.ice
        except Exception:
            pass

        elements = []

        # --- 1. En-tête : Logo / Société à gauche, Titre Facture & Date à droite ---
        left_header_flowables = []
        if getattr(company, 'logo_uri', None):
            try:
                import base64 as _b64
                uri = company.logo_uri or ''
                logo_data = None
                if uri.startswith('data:'):
                    # Data URI base64 : data:image/png;base64,<données>
                    _header, _encoded = uri.split(',', 1)
                    logo_data = _b64.b64decode(_encoded)
                elif uri.startswith('http://') or uri.startswith('https://'):
                    logo_req = urllib.request.Request(uri, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(logo_req, timeout=5) as response:
                        logo_data = response.read()
                if logo_data:
                    logo_io = io.BytesIO(logo_data)
                    rl_logo = RLImage(logo_io, width=4.0*cm, height=2.0*cm)
                    rl_logo.hAlign = 'LEFT'
                    left_header_flowables.append(rl_logo)
                    left_header_flowables.append(Spacer(1, 0.15*cm))
            except Exception:
                pass

        company_name = getattr(company, 'name', 'Mon Entreprise')
        left_header_flowables.append(Paragraph(company_name, title_style))
        if getattr(company, 'address', None):
            left_header_flowables.append(Paragraph(company.address, sub_style))
        comp_contact = []
        if getattr(company, 'phone', None): comp_contact.append(f"Tél: {company.phone}")
        if getattr(company, 'email', None): comp_contact.append(f"Email: {company.email}")
        if comp_contact:
            left_header_flowables.append(Paragraph(' | '.join(comp_contact), sub_style))

        right_header_flowables = [
            Paragraph("FACTURE", invoice_word),
            Spacer(1, 0.2*cm),
            Paragraph(f"<b>N° :</b> {order.order_num}", right_bold),
            Paragraph(f"<b>Date d'émission :</b> {order.date.strftime('%d/%m/%Y %H:%M') if order.date else '-'}", right_style),
            Paragraph(f"<b>Règlement :</b> {order.payment_method.upper()}", right_style),
            Paragraph(f"<b>Statut :</b> {'Soldée' if order.remaining_price <= 0 else 'En cours de paiement'}", right_style),
        ]

        top_table = Table([[left_header_flowables, right_header_flowables]], colWidths=[9.5*cm, 7.9*cm])
        top_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(top_table)
        elements.append(Spacer(1, 0.3*cm))
        elements.append(HRFlowable(width='100%', thickness=2, color=PRIMARY))
        elements.append(Spacer(1, 0.4*cm))

        # --- 2. Coordonnées Entreprise (Émetteur) & Client (Destinataire) ---
        seller_box = [
            Paragraph("<b>ÉMETTEUR</b>", bold_style),
            Paragraph(f"<b>{company_name}</b>", normal_style),
            Paragraph(getattr(company, 'address', '') or 'Siège social', sub_style),
            Paragraph(f"Identifiant : @{getattr(company, 'company_username', company.slug)}", sub_style),
        ]

        client_box = [
            Paragraph("<b>CLIENT (FACTURÉ À)</b>", bold_style),
            Paragraph(f"<b>{order.client_name}</b>", normal_style),
            Paragraph(f"Adresse : {client_address}", sub_style),
            Paragraph(f"Tél : {client_phone}  |  Email : {client_email}", sub_style),
        ]
        if client_ice:
            client_box.append(Paragraph(f"ICE : {client_ice}", sub_style))

        addresses_table = Table([[seller_box, client_box]], colWidths=[8.7*cm, 8.7*cm])
        addresses_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, 0), LIGHT_BG),
            ('BACKGROUND', (1, 0), (1, 0), LIGHT_BG),
            ('BOX', (0, 0), (0, 0), 0.5, BORDER_COLOR),
            ('BOX', (1, 0), (1, 0), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(addresses_table)
        elements.append(Spacer(1, 0.5*cm))

        # --- 3. Tableau des Articles ---
        elements.append(Paragraph("Détail des articles commandés", sec_title))
        items_data = [[
            Paragraph('Réf.', header_cell),
            Paragraph('Désignation', header_cell),
            Paragraph('Qté', header_cell),
            Paragraph('Prix unitaire', header_cell),
            Paragraph('Montant TTC', header_cell),
        ]]
        for item in order.items.all():
            total_line = float(item.price) * item.quantity
            items_data.append([
                Paragraph(item.product_ref or '-', normal_style),
                Paragraph(item.product_name, normal_style),
                Paragraph(str(item.quantity), ParagraphStyle('C', fontSize=8.5, alignment=TA_CENTER)),
                Paragraph(f"{float(item.price):,.2f} {currency}", right_style),
                Paragraph(f"{total_line:,.2f} {currency}", right_style),
            ])

        items_table = Table(items_data, colWidths=[2.6*cm, 7.8*cm, 1.8*cm, 2.6*cm, 2.6*cm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.4*cm))

        # --- 4. Historique des Règlements & Récapitulatif Totaux ---
        # Tableau historique des paiements à gauche
        payments = list(order.payments.all().order_by('date'))
        payment_flowables = [Paragraph("<b>Historique des règlements</b>", bold_style)]
        if payments:
            pay_rows = [[
                Paragraph('Date', ParagraphStyle('pH', fontSize=7.5, fontName='Helvetica-Bold')),
                Paragraph('Mode', ParagraphStyle('pH', fontSize=7.5, fontName='Helvetica-Bold')),
                Paragraph('Montant réglé', ParagraphStyle('pH', fontSize=7.5, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            ]]
            for p in payments:
                p_date = p.date.strftime('%d/%m/%Y %H:%M') if p.date else '-'
                pay_rows.append([
                    Paragraph(p_date, normal_style),
                    Paragraph(p.payment_method.upper(), normal_style),
                    Paragraph(f"+{float(p.amount):,.2f} {currency}", right_style),
                ])
            pay_table = Table(pay_rows, colWidths=[3.2*cm, 2.8*cm, 3.0*cm])
            pay_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            payment_flowables.append(pay_table)
        else:
            payment_flowables.append(Paragraph("Aucun versement enregistré.", sub_style))

        # Totaux à droite
        tot_rows = [
            [Paragraph('Total TTC :', right_style), Paragraph(f"<b>{float(order.total_price):,.2f} {currency}</b>", right_bold)],
            [Paragraph('Total déjà réglé :', right_style), Paragraph(f"<font color='#00A86B'><b>-{float(order.total_paid):,.2f} {currency}</b></font>", right_bold)],
            [Paragraph('<b>Reste à payer :</b>', right_bold),
             Paragraph(f"<font color='{'#00A86B' if order.remaining_price <= 0 else '#E11D48'}'><b>{float(order.remaining_price):,.2f} {currency}</b></font>", ParagraphStyle('RB', fontSize=11, fontName='Helvetica-Bold', alignment=TA_RIGHT))],
        ]
        tot_table = Table(tot_rows, colWidths=[4.6*cm, 3.8*cm])
        tot_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEABOVE', (0, 2), (-1, 2), 1, PRIMARY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        recap_table = Table([[payment_flowables, tot_table]], colWidths=[9.0*cm, 8.4*cm])
        recap_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elements.append(recap_table)
        elements.append(Spacer(1, 0.6*cm))

        # --- 5. Pied de page légal ---
        elements.append(HRFlowable(width='100%', thickness=0.8, color=BORDER_COLOR))
        elements.append(Spacer(1, 0.2*cm))
        footer_msg = f"Facture générée automatiquement par la plateforme Gestion de Stock · {company_name}"
        elements.append(Paragraph(footer_msg, ParagraphStyle('Foot', fontSize=7.5, textColor=GRAY, alignment=TA_CENTER)))

        doc.build(elements)
        return buffer.getvalue()


class InternalOrderInvoiceSendView(APIView):
    """
    POST /api/internal-orders/<pk>/invoice/send/
    Génère la facture PDF et l'envoie automatiquement à l'adresse e-mail
    enregistrée du client. Aucun e-mail n'est envoyé si le client n'a pas
    d'adresse e-mail.
    """
    permission_classes = [HasOrderPermission]

    def post(self, request, pk):
        from customers.models import Customer
        order = get_object_or_404(InternalOrder, pk=pk, company=request.user.company)

        # Récupérer l'e-mail du client enregistré en base
        client_email = None
        try:
            customer = Customer.objects.get(company=request.user.company, id=order.client_id)
            if customer.email and customer.email.strip():
                client_email = customer.email.strip()
        except Customer.DoesNotExist:
            pass

        # Si aucun e-mail enregistré pour ce client, arrêt immédiat sans déclenchement
        if not client_email:
            return Response(
                {
                    'detail': f"Le client « {order.client_name} » n'a aucune adresse e-mail enregistrée. Ajoutez un e-mail dans sa fiche client pour activer l'envoi automatique.",
                    'has_email': False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_view = InternalOrderInvoiceView()
        pdf_bytes = invoice_view._generate_pdf(order, request.user.company)

        try:
            from users.email_service import send_invoice_email
            send_invoice_email(
                to_email=client_email,
                order_num=order.order_num,
                client_name=order.client_name,
                pdf_bytes=pdf_bytes,
                company=request.user.company,
            )
        except Exception as exc:
            return Response(
                {'detail': f"Erreur lors de l'envoi de l'e-mail : {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        log_activity(
            request.user.company,
            f"Facture envoyée à {client_email} pour commande #{order.order_num}",
            "email-send-outline",
        )
        return Response({
            'detail': f"Facture #{order.order_num} envoyée avec succès à {client_email}.",
            'has_email': true if False else True,
            'recipient': client_email,
        })
