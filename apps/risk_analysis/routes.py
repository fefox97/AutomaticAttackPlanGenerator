# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import json
from datetime import datetime

from apps.authentication.models import Users
from apps.risk_analysis import blueprint
from flask import redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
from flask import current_app as app
from apps.databases.models import AttackView, Capec, MacmUser, MethodologyCatalogue, MethodologyView, ThreatCatalogue, \
    Macm, ThreatModel, ToolCatalogue, PentestPhases, ThreatAgentQuestionsReplies, ThreatAgentQuestion, ThreatAgentReply, \
    ThreatAgentReplyCategory, ThreatAgentCategory, ThreatAgentAttributesCategory, ThreatAgentAttribute, \
    ThreatAgentRiskScores, StrideImpactRecord
from sqlalchemy import func
from apps.my_modules import converter,ThreatAgentUtils
import os
import time



# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')
        if segment == '':
            segment = 'risk_analysis'
        return segment
    except:
        return None

@blueprint.route('/macm_riskRating', methods=['GET'])
@login_required
def macm_riskRating():
    threatAgentUtils= ThreatAgentUtils()
    try:
        selected_macm = request.args.get('app_id')
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        if len(table) == 0:
            table = None
    except:
        table = None
    try:
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)

    template = f"risk-analysis/macm_riskRating.html"
    return render_template(template, segment=get_segment(request), table=table,
                           threat_for_each_component=threat_for_each_component,
                           threat_number=threat_number,
                           selected_macm=selected_macm,wizard_completed=threatAgentUtils.wizard_completed(selected_macm),
                           stride_impact_completed=threatAgentUtils.stride_impact_completed(selected_macm))

@blueprint.route('/', methods=['GET'])
@login_required
def risk_analysis():
    try:
        users = Users.query.with_entities(Users.id, Users.username).where(Users.id != current_user.id).all()
        users_dict = converter.tuple_list_to_dict(users)
        usersPerApp = MacmUser.usersPerApp()
        owners = MacmUser.ownerPerApp()
        risk_analyses = MacmUser.query.filter_by(UserID=current_user.id).all()
        if len(risk_analyses) == 0:
            risk_analyses = None
    except Exception as error:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        raise error
    return render_template(f"risk-analysis/risk_analysis.html",
                           segment=get_segment(request),
                           risk_analyses=risk_analyses,
                           users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict)


@blueprint.route('/threat-agent-wizard', methods=['GET'])
@login_required
def threat_agent_wizard():
    context = {}
    appId = request.args.get('app_id')
    risk_analyses = request.args.get('risk_analyses')
    users = request.args.get('users')
    usersPerApp = request.args.get('usersPerApp')
    owners = request.args.get('owners')
    users_dict = request.args.get('users_dict')

    try:
        # Fetch all questions
        questions = ThreatAgentQuestion.query.all()

        # Initialize list to store question and its replies
        questions_replies_list = []

        # Loop through questions
        for question in questions:
            replies = []
            # Fetch replies for the current question
            question_replies = ThreatAgentQuestionsReplies.query.filter_by(Question_id=question.Id).all()
            for question_reply in question_replies:
                reply_id = question_reply.Reply_id
                # Fetch the ThreatAgentReply
                reply = ThreatAgentReply.query.filter_by(Id=reply_id).first()
                if reply:
                    replies.append({
                        'id': reply.Id,  # ID della risposta
                        'text': reply.Reply,  # Testo della risposta
                        'multiple': reply.Multiple,  # Indica se è multipla o no
                        'details': reply.Details  # Dettagli della risposta
                    })

            # Add question and corresponding replies to the list
            questions_replies_list.append({
                'id': question.Id,  # ID della domanda
                'question': question.Question,
                'replies': replies
            })

        # Add the questions and replies to the context
        context['questions_replies'] = questions_replies_list
        context['appId'] = appId

        print(questions_replies_list)

    except Exception as e:
        app.logger.error(f"Error occurred while fetching questions or replies: {e}", exc_info=True)
        context['questions_replies'] = None

    # Render the template with the context data
    return render_template(
        "risk-analysis/threat_agent_wizard.html",
        segment=get_segment(request),
        risk_analyses=risk_analyses,
        users=users,
        usersPerApp=usersPerApp,
        owners=owners,
        users_dict=users_dict,
        questions_replies=questions_replies_list,
        appId=appId
    )

@blueprint.route('/submit-questionnaire', methods=['POST'])
@login_required
def submit_questionnaire():
    if request.method == 'POST':
        threatAgentUtils= ThreatAgentUtils()
        # Initialize a dictionary to store the user's responses
        user_responses = {}
        appId = request.form.get('appId')
        # Loop through the POST data to collect answers for each question
        for key, value in request.form.items():
            # The question ID is embedded in the "name" attribute, so we extract it
            if key.startswith('question_'):
                question_id = key.split('_')[1]

                # If the key ends with '[]', it means this is a multiple choice question (checkboxes)
                if '[]' in key:
                    # Remove '[]' from the key
                    question_id = question_id.replace('[]', '')
                    user_responses[question_id] = request.form.getlist(key)
                else:
                    user_responses[question_id] = value

        # Question Number 1
        Q1 = user_responses['1']
        Q1relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q1).all()

        # Question Number 2
        Q2 = user_responses['2']
        Q2relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q2).all()

        # Question Number 3
        Q3s = user_responses['3']
        Q3sResults = []
        for Q3 in Q3s:
            Q3relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q3).all()
            Q3sResults.append(set(Q3relatedCategories))  # Convert to set for easier merging

        # Unione progressiva per Q3
        Q3Merged = Q3sResults[0] if Q3sResults else set()
        for Q3Result in Q3sResults[1:]:
            Q3Merged = Q3Merged.union(Q3Result)

        # Question Number 4
        Q4s = user_responses['4']
        Q4sResults = []
        for Q4 in Q4s:
            Q4relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q4).all()
            Q4sResults.append(set(Q4relatedCategories))  # Convert to set for easier merging

        # Unione progressiva per Q4
        Q4Merged = Q4sResults[0] if Q4sResults else set()
        for Q4Result in Q4sResults[1:]:
            Q4Merged = Q4Merged.union(Q4Result)


        ThreatAgents=Q1relatedCategories
        ThreatAgents = threatAgentUtils.intersect_threat_agents(ThreatAgents, set(Q2relatedCategories))
        ThreatAgents = threatAgentUtils.intersect_threat_agents(ThreatAgents, Q3Merged)
        ThreatAgents = threatAgentUtils.intersect_threat_agents(ThreatAgents, Q4Merged)
        ThreatAgents= threatAgentUtils.remove_duplicates_by_category_id(ThreatAgents)
        ThreatAgentsList=[]
        for threatAgent in ThreatAgents:
            category = ThreatAgentCategory.query.filter_by(Id=threatAgent.Category_id).first()
            if category:
                attributes=[]
                AttributesCategory = ThreatAgentAttributesCategory.query.filter_by(Category_id=category.Id).all()
                for attribute_category in AttributesCategory:
                    attribute=ThreatAgentAttribute.query.filter_by(Id=attribute_category.Attribute_id).first()
                    attributes.append(attribute)
                ThreatAgentsList.append({
                    'category': category,
                    'attributes': attributes
                })
        # Process the responses and generate threat agents based on the responses
        # threat_agents = generate_threat_agents(user_responses)

        # Pass the generated threat agents to the template
        return render_template(
            "risk-analysis/threat_agent_rating.html",
            segment=get_segment(request),
            user_responses=user_responses,
            ThreatAgents=ThreatAgentsList,
            appId=appId
        )


@blueprint.route('/threat_agent_evaluation', methods=['POST'])
@login_required
def threat_agent_evaluation():
    """
    Endpoint to evaluate threat agents for a given application and calculate OWASP risk scores.
    """
    # Extract `appId` and `objective` from the form
    threatAgentUtils= ThreatAgentUtils()
    objective = request.form.get('objective', 'riskanalysis')  # Default to 'riskanalysis'
    appId = request.form.get('appId')

    # Initialize variables for reports and data analysis
    reports = []
    table = None
    attack_for_each_component = None
    attack_number = 0
    threat_for_each_component = None
    threat_number = 0

    try:
        # Fetch distinct reports for the given `appId`
        reports = (
            AttackView.query.filter_by(AppID=appId)
            .with_entities(
                AttackView.Attack_Number,
                AttackView.Tool_ID,
                AttackView.Tool_Name,
                AttackView.Attack_Pattern,
                AttackView.Capec_ID,
                AttackView.Threat_ID,
                AttackView.Asset_Type,
                AttackView.Threat,
                AttackView.Component_ID,
                AttackView.Asset,
                AttackView.AppID,
                AttackView.ReportFiles,
                AttackView.Report_Parser
            )
            .where(AttackView.ReportFiles.isnot(None))
            .distinct()
            .all()
        )

        # Fetch table data for the given `appId`
        table = Macm.query.filter_by(App_ID=appId).all()
        if not table:
            table = None
    except Exception as e:
        app.logger.error(f"Error fetching reports or table for appId {appId}: {e}", exc_info=True)

    try:
        # Count attacks and threats for each component
        attack_for_each_component = AttackView.query.filter_by(AppID=appId).with_entities(
            AttackView.Component_ID, func.count(AttackView.Component_ID)
        ).group_by(AttackView.Component_ID).all()
        attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)

        attack_number = AttackView.query.filter_by(AppID=appId).count()

        threat_for_each_component = ThreatModel.query.filter_by(AppID=appId).with_entities(
            ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)
        ).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)

        threat_number = ThreatModel.query.filter_by(AppID=appId).count()
    except Exception as e:
        app.logger.error(f"Error fetching attacks or threats for appId {appId}: {e}", exc_info=True)

    # OWASP scoring variables
    OWASP_Motive_Total = 0
    OWASP_Size_Total = 0
    OWASP_Opportunity_Total = 0
    OWASP_Skill_Total = 0
    total_weights = 0
    category_details_list = []

    try:
        # Dictionaries to store category, attribute, and rating data
        category_ids = {}
        attribute_ids = {}
        ratings = {}
        rating_map = {'L': 1, 'M': 2, 'H': 3}  # Risk level mapping

        # Parse category, attribute, and rating information from the form
        for key in request.form.keys():
            if key.startswith("categoryId_"):
                category_name = key.split("categoryId_")[1]
                category_ids[category_name] = request.form.get(key)
            elif key.startswith("attributeId_"):
                parts = key.split("_")
                category_name = parts[1]
                attribute_name = "_".join(parts[2:])
                if category_name not in attribute_ids:
                    attribute_ids[category_name] = {}
                attribute_ids[category_name][attribute_name] = request.form.get(key)
            elif key.startswith("rating_"):
                category_name = key.split("rating_")[1]
                ratings[category_name] = request.form.get(key)

        # Process each category and calculate OWASP risk scores
        for category_name, category_id in category_ids.items():
            category_details = {}

            # Fetch the category and its attributes from the database
            category = ThreatAgentCategory.query.filter_by(Id=category_id).first()
            if not category:
                continue  # Skip invalid categories

            category_attributes = ThreatAgentAttributesCategory.query.filter_by(Category_id=category.Id).all()
            attributes = [
                ThreatAgentAttribute.query.filter_by(Id=attr.attribute_id).first()
                for attr in category_attributes
            ]

            # Calculate OWASP parameters based on attribute scores
            rating = ratings.get(category_name)
            rating_score = rating_map.get(rating, 0)
            motive = size = opportunity = skill = 0
            limits = intent = access = resources = visibility = skills = 0

            for attribute in attributes:
                if attribute.attribute == 'Skills':
                    skills = attribute.score
                elif attribute.attribute == 'Resources':
                    resources = attribute.score
                elif attribute.attribute == 'Visibility':
                    visibility = attribute.score
                elif attribute.attribute == 'Limits':
                    limits = attribute.score
                elif attribute.attribute == 'Intent':
                    intent = attribute.score
                elif attribute.attribute == 'Access':
                    access = attribute.score

            # Compute individual OWASP parameters
            motive = ((((intent / 2) + (limits / 4)) / 2) * 10)
            opportunity = ((((access / 2) + (resources / 6) + (visibility / 4)) / 3) * 10)
            size = (resources / 6) * 10
            skill = (skills / 4) * 10

            # Accumulate weighted totals
            OWASP_Motive_Total += motive * rating_score
            OWASP_Opportunity_Total += opportunity * rating_score
            OWASP_Size_Total += size * rating_score
            OWASP_Skill_Total += skill * rating_score
            total_weights += rating_score

        # Normalize scores based on total weights
        if total_weights > 0:
            OWASP_Motive_Total = int(round(OWASP_Motive_Total / total_weights))
            OWASP_Opportunity_Total = int(round(OWASP_Opportunity_Total / total_weights))
            OWASP_Size_Total = int(round(OWASP_Size_Total / total_weights))
            OWASP_Skill_Total = int(round(OWASP_Skill_Total / total_weights))
        else:
            OWASP_Motive_Total = OWASP_Opportunity_Total = OWASP_Size_Total = OWASP_Skill_Total = 0

        # Save calculated scores to the database
        risk_score = ThreatAgentRiskScores.query.filter_by(AppID=appId).first()
        if risk_score:
            risk_score.motive = OWASP_Motive_Total
            risk_score.opportunity = OWASP_Opportunity_Total
            risk_score.size = OWASP_Size_Total
            risk_score.skill = OWASP_Skill_Total
        else:
            risk_score = ThreatAgentRiskScores(
                AppID=appId,
                Motive=OWASP_Motive_Total,
                Opportunity=OWASP_Opportunity_Total,
                Size=OWASP_Size_Total,
                Skill=OWASP_Skill_Total,
                Created_at=datetime.utcnow(),
                Uploaded_at=datetime.utcnow()
            )

            risk_score.save()

    except Exception as e:
        app.logger.error(f"Error processing threat agent evaluation: {e}", exc_info=True)

    # Render the appropriate template
    template = "risk-analysis/macm_riskRating.html"
    return render_template(
        template,
        segment=get_segment(request),
        table=table,
        attack_for_each_component=attack_for_each_component,
        attack_number=attack_number,
        threat_for_each_component=threat_for_each_component,
        threat_number=threat_number,
        reports=reports,
        appId=appId,
        wizard_completed=True,
        stride_impact_completed=threatAgentUtils.stride_impact_completed(appId)
    )


@blueprint.route('/stride-impact-rating', methods=['GET'])
@login_required
def stride_impact_rating():
    """
    Endpoint to evaluate STRIDE impact for a given application.
    """
    # Extract `appId` and `objective` from the form
    objective = request.args.get('objective', 'riskanalysis')
    appId = request.args.get('app_id')

    template = "risk-analysis/stride_impact_risk.html"
    return render_template(
        template,
        segment=get_segment(request),appId=appId, objective=objective
    )

@blueprint.route('/stride_impact_evaluation', methods=['POST'])
@login_required
def stride_impact_evaluation():
    threatAgentUtils= ThreatAgentUtils()
    """
    Endpoint to evaluate STRIDE impact for a given application.
    """
    objective = request.form.get('objective', 'riskanalysis')  # Default to 'riskanalysis'
    appId = request.form.get('appId')
    print(f"applicazione: {appId}")

    # Initialize variables for reports and data analysis
    reports = []
    table = None
    attack_for_each_component = None
    attack_number = 0
    threat_for_each_component = None
    threat_number = 0

    try:
        # Fetch distinct reports for the given `appId`
        reports = (
            AttackView.query.filter_by(AppID=appId)
            .with_entities(
                AttackView.Attack_Number,
                AttackView.Tool_ID,
                AttackView.Tool_Name,
                AttackView.Attack_Pattern,
                AttackView.Capec_ID,
                AttackView.Threat_ID,
                AttackView.Asset_Type,
                AttackView.Threat,
                AttackView.Component_ID,
                AttackView.Asset,
                AttackView.AppID,
                AttackView.ReportFiles,
                AttackView.Report_Parser
            )
            .where(AttackView.ReportFiles.isnot(None))
            .distinct()
            .all()
        )

        # Fetch table data for the given `appId`
        table = Macm.query.filter_by(App_ID=appId).all()
        if not table:
            table = None
    except Exception as e:
        app.logger.error(f"Error fetching reports or table for appId {appId}: {e}", exc_info=True)

    try:
        # Count attacks and threats for each component
        attack_for_each_component = AttackView.query.filter_by(AppID=appId).with_entities(
            AttackView.Component_ID, func.count(AttackView.Component_ID)
        ).group_by(AttackView.Component_ID).all()
        attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)

        attack_number = AttackView.query.filter_by(AppID=appId).count()

        threat_for_each_component = ThreatModel.query.filter_by(AppID=appId).with_entities(
            ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)
        ).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)

        threat_number = ThreatModel.query.filter_by(AppID=appId).count()
    except Exception as e:
        app.logger.error(f"Error fetching attacks or threats for appId {appId}: {e}", exc_info=True)


    # STRIDE categories
    strides = ['spoofing', 'tampering', 'reputation', 'information_disclosure', 'dos', 'elevationofprivileges']
    stride_data = {}

    # Manually mapping specific strides to the correct readable format
    mapping = {
        'spoofing': 'Spoofing',
        'tampering': 'Tampering',
        'reputation': 'Reputation',
        'information_disclosure': 'Information Disclosure',
        'dos': 'Denial of Service',
        'elevationofprivileges': 'Elevation of Privileges'
    }

    for stride in strides:
        stride_data[stride] = {
            "financialdamage": int(request.form.get(f"{stride}_financialdamage", 0)),
            "reputationdamage": int(request.form.get(f"{stride}_reputationdamage", 0)),
            "noncompliance": int(request.form.get(f"{stride}_noncompliance", 0)),
            "privacyviolation": int(request.form.get(f"{stride}_privacyviolation", 0)),
        }

    for stride, impacts in stride_data.items():
        print(f"Processing STRIDE category: {stride}")
        print(f"Financial Damage: {impacts['financialdamage']}")
        print(f"Reputation Damage: {impacts['reputationdamage']}")
        print(f"Non-compliance: {impacts['noncompliance']}")
        print(f"Privacy Violation: {impacts['privacyviolation']}")

        # Usa il metodo per aggiornare o creare il record
        StrideImpactRecord.update_or_create(
            app_id=appId,
            stride=stride,
            financialdamage=impacts['financialdamage'],
            reputationdamage=impacts['reputationdamage'],
            noncompliance=impacts['noncompliance'],
            privacyviolation=impacts['privacyviolation']
        )

    template = "risk-analysis/macm_riskRating.html"
    return render_template(
        template,
        segment=get_segment(request),
        table=table,
        attack_for_each_component=attack_for_each_component,
        attack_number=attack_number,
        threat_for_each_component=threat_for_each_component,
        threat_number=threat_number,
        reports=reports,
        appId=appId,
        objective=objective,
        wizard_completed=threatAgentUtils.wizard_completed(appId),
        stride_impact_completed=threatAgentUtils.stride_impact_completed(appId)
    )

@blueprint.route('/macm-detailRisk', methods=['GET'])
def macm_riskDetailed():
    threatAgentUtils = ThreatAgentUtils()
    try:
        selected_macm = request.args.get('app_id')
        selected_id = request.args.get('id')
        macm_data = Macm.query.filter_by(Component_ID=selected_id, App_ID=selected_macm).first()
        threat_data = ThreatModel.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
        methodologies_data = MethodologyView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
        attack_data = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
        pentest_phases = PentestPhases.query.all()
        av_pentest_phases = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).with_entities(AttackView.PhaseID, AttackView.PhaseName).distinct().order_by(AttackView.PhaseID).all()
    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)

    ThreatAgentParameters= ThreatAgentRiskScores.query.filter_by(AppID=selected_macm).first()
    #calcolo stride impct
    form_data = {}
    form_data['size']=ThreatAgentParameters.Size
    form_data['motive']=ThreatAgentParameters.Motive
    form_data['opportunity']=ThreatAgentParameters.Opportunity
    form_data['skill']=ThreatAgentParameters.Skill

    # Iterate through each threat
    for threat in threat_data:

        # Initialize a dictionary to track maximum values and corresponding details for each category
        category_max = {
            "Financialdamage": {"max_value": 0, "stride": None, "record": None},
            "Reputationdamage": {"max_value": 0, "stride": None, "record": None},
            "Noncompliance": {"max_value": 0, "stride": None, "record": None},
            "Privacyviolation": {"max_value": 0, "stride": None, "record": None},
        }

        # Iterate over each STRIDE element for the threat
        for stride in threatAgentUtils.reverse_map_stride(threat.STRIDE):
            stride_impact = StrideImpactRecord.query.filter_by(AppID=selected_macm, Stride=stride).first()

            if stride_impact:
                # Update maximums and store details for each category
                for category in category_max.keys():
                    current_value = getattr(stride_impact, category)
                    if current_value > category_max[category]["max_value"]:
                        category_max[category] = {
                            "max_value": current_value,
                            "stride": stride,
                            "record": stride_impact,
                        }

        # Store detailed results for the threat
        form_data[threat.Threat] = {
            "threat": threat.Threat,
            "description": threat.Description,
            "stride": threatAgentUtils.map_stride(threat.STRIDE),
            "financialdamage": category_max["Financialdamage"]["max_value"],
            "reputationdamage": category_max["Reputationdamage"]["max_value"],
            "noncompliance": category_max["Noncompliance"]["max_value"],
            "privacyviolation": category_max["Privacyviolation"]["max_value"],
        }

        #set catalogue-based parameters 'ease_of_discovery', 'ease_of_exploit', 'awareness', 'intrusion_detection']
        form_data[threat.Threat]['ease_of_discovery']=threat.EasyOfDiscovery
        form_data[threat.Threat]['ease_of_exploit']=threat.EasyOfExploit
        form_data[threat.Threat]['awareness']=threat.Awareness
        form_data[threat.Threat]['intrusion_detection']=threat.IntrusionDetection
        form_data[threat.Threat]['loss_of_confidentiality']=threat.LossOfConfidentiality
        form_data[threat.Threat]['loss_of_integrity']=threat.LossOfIntegrity
        form_data[threat.Threat]['loss_of_availability']=threat.LossOfAvailability
        form_data[threat.Threat]['loss_of_accountability']=threat.LossOfAccountability

    return render_template(f"risk-analysis/macm-detailRisk.html", segment=get_segment(request),
                           selected_macm=selected_macm, component_id=selected_id,
                           macm_data=macm_data, attack_data=attack_data, pentest_phases=pentest_phases,
                           av_pentest_phases=av_pentest_phases, threat_data=threat_data,
                           methodologies_data=methodologies_data, ThreatAgentParameters=ThreatAgentParameters, form_data=form_data)

@blueprint.route('/save_risk_evaluation', methods=['POST'])
def save_risk_evaluation():
    threatAgentUtils= ThreatAgentUtils()
    try:
        selected_macm = request.form.get('selected_macm')
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        if len(table) == 0:
            table = None
    except:
        table = None
    try:
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
    try:
        component_id = request.form.get('component_id')
        selected_macm = request.form.get('selected_macm')
        # Controllo se il campo 'evaluation_data' esiste nella richiesta
        evaluation_data_json = request.form.get('evaluation_data', None)
        if not evaluation_data_json:
            raise ValueError("Il campo 'evaluation_data' non è stato fornito nella richiesta.")

        # Verifica che il campo contenga JSON valido
        try:
            evaluation_data = json.loads(evaluation_data_json)
            print("Dati evaluation_data decodificati:", evaluation_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Il campo 'evaluation_data' contiene JSON non valido: {e}")

    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)


    template = f"risk-analysis/macm_riskRating.html"
    return render_template(template, segment=get_segment(request), table=table,
                           threat_for_each_component=threat_for_each_component,
                           threat_number=threat_number,
                           selected_macm=selected_macm,wizard_completed=threatAgentUtils.wizard_completed(selected_macm),
                           stride_impact_completed=threatAgentUtils.stride_impact_completed(selected_macm))
