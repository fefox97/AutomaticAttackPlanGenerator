# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from datetime import datetime

from apps.authentication.models import Users
from apps.home import blueprint
from flask import redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
from flask import current_app as app
from apps.databases.models import AttackView, Capec, MacmUser, MethodologyCatalogue, MethodologyView, ThreatCatalogue, \
    Macm, ThreatModel, ToolCatalogue, PentestPhases, ThreatAgentQuestionsReplies, ThreatAgentQuestion, ThreatAgentReply, \
    ThreatAgentReplyCategory, ThreatAgentCategory, ThreatAgentAttributesCategory, ThreatAgentAttribute, \
    ThreatAgentRiskScores, StrideImpactRecord
from sqlalchemy import func
from apps.my_modules import converter
import os
import time


@blueprint.route('/index')
@login_required
def index():
    return redirect(url_for('home_blueprint.penetration_tests'))

@blueprint.route('/capec', methods=['GET'])
@login_required
def capec():
    try:
        table = Capec.query.order_by(Capec.abstraction_order, Capec.Capec_ID).all()
        meta_attack_pattern_number = Capec.query.filter(Capec.Abstraction=='Meta').count()
        standard_attack_pattern_number = Capec.query.filter(Capec.Abstraction=='Standard').count()
        detailed_attack_pattern_number = Capec.query.filter(Capec.Abstraction=='Detailed').count()
        if len(table) == 0:
            table = None
            meta_attack_pattern_number = None
            standard_attack_pattern_number = None
            detailed_attack_pattern_number = None
    except:
        table = None
        meta_attack_pattern_number = None
        standard_attack_pattern_number = None
        detailed_attack_pattern_number = None
    return render_template(f"home/capec.html", segment=get_segment(request), table=table, meta_attack_pattern_number=meta_attack_pattern_number, standard_attack_pattern_number=standard_attack_pattern_number, detailed_attack_pattern_number=detailed_attack_pattern_number)

@blueprint.route('/capec-detail', methods=['GET'])
@login_required
def capec_detail():
    selected_id = request.args.get('id')
    selected_attack_pattern = Capec.query.filter_by(Capec_ID=selected_id).first()
    return render_template(f"home/capec-detail.html", segment=get_segment(request), data=selected_attack_pattern)

@blueprint.route('/threat-catalog', methods=['GET'])
@login_required
def threat_catalog():
    try:
        table = ThreatCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"home/threat-catalog.html", segment=get_segment(request), table=table)

@blueprint.route('/tools', methods=['GET'])
@login_required
def tools():
    try:
        table = ToolCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"home/tools.html", segment=get_segment(request), table=table)

@blueprint.route('/methodologies', methods=['GET'])
@login_required
def methodologies():
    try:
        table = MethodologyCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"home/methodologies.html", segment=get_segment(request), table=table)

@blueprint.route('/penetration-tests', methods=['GET'])
@login_required
def penetration_tests():
    try:
        users = Users.query.with_entities(Users.id, Users.username).where(Users.id != current_user.id).all()
        users_dict = converter.tuple_list_to_dict(users)
        usersPerApp = MacmUser.usersPerApp()
        owners = MacmUser.ownerPerApp()
        pentests = MacmUser.query.filter_by(UserID=current_user.id).all()
        if len(pentests) == 0:
            pentests = None
    except Exception as error:
        pentests = None
        raise error
    return render_template(f"home/penetration-tests.html", segment=get_segment(request), pentests=pentests, users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict)

@blueprint.route('/macm', methods=['GET','POST'])
def macm():
    try:
        selected_macm = request.args.get('app_id')
        objective = request.args.get('objective')
        reports = AttackView.query.filter_by(AppID=selected_macm).with_entities(AttackView.Attack_Number, AttackView.Tool_ID, AttackView.Tool_Name, AttackView.Attack_Pattern, AttackView.Capec_ID, AttackView.Threat_ID, AttackView.Asset_Type, AttackView.Threat, AttackView.Component_ID, AttackView.Asset, AttackView.AppID, AttackView.ReportFiles, AttackView.Report_Parser).where(AttackView.ReportFiles.isnot(None)).distinct().all()
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        if len(table) == 0:
            table = None
    except:
        table = None
    try:
        attack_for_each_component = AttackView.query.filter_by(AppID=selected_macm).with_entities(AttackView.Component_ID, func.count(AttackView.Component_ID)).group_by(AttackView.Component_ID).all()
        attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)
        attack_number = AttackView.query.filter_by(AppID=selected_macm).count()
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        attack_for_each_component = None
        attack_number = None

    template = f"home/macm_riskRating.html" if objective == "riskanalysis" else f"home/macm.html"
    return render_template(template, segment=get_segment(request), table=table,
                           attack_for_each_component=attack_for_each_component,
                           attack_number=attack_number,
                           threat_for_each_component=threat_for_each_component,
                           threat_number=threat_number, reports=reports,
                           selected_macm=selected_macm,wizard_completed=wizard_completed(selected_macm),
                           stride_impact_completed=stride_impact_completed(selected_macm))

@blueprint.route('/macm-detail', methods=['GET'])
def macm_detail():
    selected_macm = request.args.get('app_id')
    selected_id = request.args.get('id')
    macm_data = Macm.query.filter_by(Component_ID=selected_id, App_ID=selected_macm).first()
    threat_data = ThreatModel.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    methodologies_data = MethodologyView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    attack_data = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    pentest_phases = PentestPhases.query.all()
    av_pentest_phases = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).with_entities(AttackView.PhaseID, AttackView.PhaseName).distinct().order_by(AttackView.PhaseID).all()
    return render_template(f"home/macm-detail.html", segment=get_segment(request), macm_data=macm_data, attack_data=attack_data, pentest_phases=pentest_phases, av_pentest_phases=av_pentest_phases, threat_data=threat_data, methodologies_data=methodologies_data)

@blueprint.route('/settings', methods=['GET'])
def settings():
    excel_file = app.config['THREAT_CATALOG_FILE_NAME']
    path = app.config['DBS_PATH']
    if not os.path.exists(f'{path}/{excel_file}'):
        excel_file = None
    try:
        last_modified = time.ctime(os.path.getmtime(f'{path}/{excel_file}'))
    except:
        last_modified = None
    return render_template(f"admin/settings.html", segment=get_segment(request), excel_file=excel_file, last_modified=last_modified)

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None


@blueprint.route('/risk_analysis', methods=['GET'])
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
        risk_analyses = None
        raise error
    return render_template(f"home/risk_analysis.html",
                           segment=get_segment(request),
                           risk_analyses=risk_analyses,
                           users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict)


@blueprint.route('/threat-agent-wizard', methods=['GET'])
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
            question_replies = ThreatAgentQuestionsReplies.query.filter_by(question_id=question.Id).all()
            for question_reply in question_replies:
                reply_id = question_reply.reply_id
                # Fetch the ThreatAgentReply
                reply = ThreatAgentReply.query.filter_by(id=reply_id).first()
                if reply:
                    replies.append({
                        'id': reply.id,  # ID della risposta
                        'text': reply.reply,  # Testo della risposta
                        'multiple': reply.multiple  # Indica se è multipla o no
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

    except Exception as e:
        app.logger.error(f"Error occurred while fetching questions or replies: {e}", exc_info=True)
        context['questions_replies'] = None

    # Render the template with the context data
    return render_template(
        "home/threat_agent_wizard.html",
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
def submit_questionnaire():
    if request.method == 'POST':
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
        Q1relatedCategories = ThreatAgentReplyCategory.query.filter_by(reply_id=Q1).all()

        # Question Number 2
        Q2 = user_responses['2']
        Q2relatedCategories = ThreatAgentReplyCategory.query.filter_by(reply_id=Q2).all()

        # Question Number 3
        Q3s = user_responses['3']
        Q3sResults = []
        for Q3 in Q3s:
            Q3relatedCategories = ThreatAgentReplyCategory.query.filter_by(reply_id=Q3).all()
            Q3sResults.append(set(Q3relatedCategories))  # Convert to set for easier merging

        # Unione progressiva per Q3
        Q3Merged = Q3sResults[0] if Q3sResults else set()
        for Q3Result in Q3sResults[1:]:
            Q3Merged = Q3Merged.union(Q3Result)

        # Question Number 4
        Q4s = user_responses['4']
        Q4sResults = []
        for Q4 in Q4s:
            Q4relatedCategories = ThreatAgentReplyCategory.query.filter_by(reply_id=Q4).all()
            Q4sResults.append(set(Q4relatedCategories))  # Convert to set for easier merging

        # Unione progressiva per Q4
        Q4Merged = Q4sResults[0] if Q4sResults else set()
        for Q4Result in Q4sResults[1:]:
            Q4Merged = Q4Merged.union(Q4Result)

        ThreatAgents=Q1relatedCategories
        ThreatAgents = intersect_threat_agents(ThreatAgents, set(Q2relatedCategories))
        ThreatAgents = intersect_threat_agents(ThreatAgents, Q3Merged)
        ThreatAgents = intersect_threat_agents(ThreatAgents, Q4Merged)
        ThreatAgents= remove_duplicates_by_category_id(ThreatAgents)
        ThreatAgentsList=[]
        for threatAgent in ThreatAgents:
            category = ThreatAgentCategory.query.filter_by(Id=threatAgent.category_id).first()
            if category:
                attributes=[]
                AttributesCategory = ThreatAgentAttributesCategory.query.filter_by(category_id=category.Id).all()
                for attribute_category in AttributesCategory:
                    attribute=ThreatAgentAttribute.query.filter_by(Id=attribute_category.attribute_id).first()
                    attributes.append(attribute)
                ThreatAgentsList.append({
                    'category': category,
                    'attributes': attributes
                })
        # Process the responses and generate threat agents based on the responses
        # threat_agents = generate_threat_agents(user_responses)

        # Pass the generated threat agents to the template
        return render_template(
            "home/threat_agent_rating.html",
            segment=get_segment(request),
            user_responses=user_responses,
            ThreatAgents=ThreatAgentsList,
            appId=appId
        )


@blueprint.route('/threat_agent_evaluation', methods=['POST'])
def threat_agent_evaluation():
    """
    Endpoint to evaluate threat agents for a given application and calculate OWASP risk scores.
    """
    # Extract `appId` and `objective` from the form
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

            category_attributes = ThreatAgentAttributesCategory.query.filter_by(category_id=category.Id).all()
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
        risk_score = ThreatAgentRiskScores.query.filter_by(appID=appId).first()
        if risk_score:
            risk_score.motive = OWASP_Motive_Total
            risk_score.opportunity = OWASP_Opportunity_Total
            risk_score.size = OWASP_Size_Total
            risk_score.skill = OWASP_Skill_Total
        else:
            risk_score = ThreatAgentRiskScores(
                appID=appId,
                motive=OWASP_Motive_Total,
                opportunity=OWASP_Opportunity_Total,
                size=OWASP_Size_Total,
                skill=OWASP_Skill_Total,
                created_at=datetime.utcnow(),
                uploaded_at=datetime.utcnow()
            )

            risk_score.save()

    except Exception as e:
        app.logger.error(f"Error processing threat agent evaluation: {e}", exc_info=True)

    # Render the appropriate template
    template = "home/macm_riskRating.html" if objective == "riskanalysis" else "home/macm.html"
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
        wizard_completed=True
    )


@blueprint.route('/stride-impact-rating', methods=['GET'])
def stride_impact_rating():
    """
    Endpoint to evaluate STRIDE impact for a given application.
    """
    # Extract `appId` and `objective` from the form
    objective = request.args.get('objective', 'riskanalysis')
    appId = request.args.get('app_id')

    template = "home/stride_impact_risk.html" if objective == "riskanalysis" else "home/macm.html"
    return render_template(
        template,
        segment=get_segment(request),appId=appId, objective=objective
    )

@blueprint.route('/stride_impact_evaluation', methods=['POST'])
def stride_impact_evaluation():
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

    template = "home/macm_riskRating.html" if objective == "riskanalysis" else "home/macm.html"
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
        wizard_completed=wizard_completed(appId),
        stride_impact_completed=stride_impact_completed(appId)
    )


def merge_threat_agent_reply_categories(sets):
    """
    Unisce insiemi di oggetti ThreatAgentReplyCategory evitando duplicati.

    :param sets: Lista di liste di oggetti ThreatAgentReplyCategory
    :return: Lista unita senza duplicati
    """
    unique_items = {}
    result = []

    for category_set in sets:
        for category in category_set:
            # Crea una chiave unica basata sugli attributi principali
            unique_key = (category.id, category.reply_id, category.category_id)
            if unique_key not in unique_items:
                unique_items[unique_key] = category
                result.append(category)

    return result

def intersect_threat_agents(set1, set2):
    """
    Restituisce la lista di ThreatAgentReplyCategory comuni tra due insiemi,
    basata esclusivamente sul campo 'category_id'.

    :param set1: Primo insieme di ThreatAgentReplyCategory
    :param set2: Secondo insieme di ThreatAgentReplyCategory
    :return: Lista di ThreatAgentReplyCategory comuni per 'category_id'
    """
    # Crea un dizionario per il primo set basato su 'category_id'
    set1_dict = {category.category_id: category for category in set1}

    # Trova le categorie comuni tra set1 e set2 in base a 'category_id'
    common_categories = [
        category for category in set2
        if category.category_id in set1_dict
    ]

    return common_categories


def remove_duplicates_by_category_id(threat_agent_set):
    """
    Rimuove duplicati da un set basandosi sul campo 'category_id'.

    :param threat_agent_set: Insieme di ThreatAgentReplyCategory
    :return: Set senza duplicati basato su 'category_id'
    """
    unique_categories = {}

    # Itera sugli oggetti del set
    for category in threat_agent_set:
        # Usa 'category_id' come chiave per mantenere solo un'istanza per ID
        unique_categories[category.category_id] = category

    # Ritorna i valori unici come un set
    return set(unique_categories.values())

def wizard_completed(appId):

    # Check if the ThreatAgentRiskScore exists for the application
    completed= False
    threat_agent_score = ThreatAgentRiskScores.query.filter_by(appID=appId).first()
    if threat_agent_score:
        completed= True
    return completed

def stride_impact_completed(appId):
    # Check if the STRIDE impact records exist for the application
    stride_impact_records = StrideImpactRecord.query.filter_by(appID=appId).all()
    return len(stride_impact_records) > 5

@blueprint.route('/macm-risk', methods=['GET'])
def macm_risk():
    try:
        selected_macm = request.args.get('app_id')
        objective = request.args.get('objective')
        reports = AttackView.query.filter_by(AppID=selected_macm).with_entities(AttackView.Attack_Number, AttackView.Tool_ID, AttackView.Tool_Name, AttackView.Attack_Pattern, AttackView.Capec_ID, AttackView.Threat_ID, AttackView.Asset_Type, AttackView.Threat, AttackView.Component_ID, AttackView.Asset, AttackView.AppID, AttackView.ReportFiles, AttackView.Report_Parser).where(AttackView.ReportFiles.isnot(None)).distinct().all()
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        if len(table) == 0:
            table = None
    except:
        table = None
    try:
        attack_for_each_component = AttackView.query.filter_by(AppID=selected_macm).with_entities(AttackView.Component_ID, func.count(AttackView.Component_ID)).group_by(AttackView.Component_ID).all()
        attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)
        attack_number = AttackView.query.filter_by(AppID=selected_macm).count()
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        attack_for_each_component = None
        attack_number = None

    template = f"home/macm_riskRating.html"
    return render_template(template, segment=get_segment(request), table=table,
                           attack_for_each_component=attack_for_each_component,
                           attack_number=attack_number,
                           threat_for_each_component=threat_for_each_component,
                           threat_number=threat_number, reports=reports,
                           selected_macm=selected_macm,wizard_completed=wizard_completed(selected_macm),
                           stride_impact_completed=stride_impact_completed(selected_macm))

@blueprint.route('/macm-detailRisk', methods=['GET'])
def macm_riskDetailed():
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

    ThreatAgentParameters= ThreatAgentRiskScores.query.filter_by(appID=selected_macm).first()
    #calcolo stride impct
    form_data = {}
    form_data['size']=ThreatAgentParameters.size
    form_data['motive']=ThreatAgentParameters.motive
    form_data['opportunity']=ThreatAgentParameters.opportunity
    form_data['skill']=ThreatAgentParameters.skill

    # Iterate through each threat
    for threat in threat_data:

        # Initialize a dictionary to track maximum values and corresponding details for each category
        category_max = {
            "financialdamage": {"max_value": 0, "stride": None, "record": None},
            "reputationdamage": {"max_value": 0, "stride": None, "record": None},
            "noncompliance": {"max_value": 0, "stride": None, "record": None},
            "privacyviolation": {"max_value": 0, "stride": None, "record": None},
        }

        # Iterate over each STRIDE element for the threat
        for stride in reverse_map_stride(threat.STRIDE):
            stride_impact = StrideImpactRecord.query.filter_by(appID=selected_macm, stride=stride).first()

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
            "stride": map_stride(threat.STRIDE),
            "financialdamage": category_max["financialdamage"]["max_value"],
            "reputationdamage": category_max["reputationdamage"]["max_value"],
            "noncompliance": category_max["noncompliance"]["max_value"],
            "privacyviolation": category_max["privacyviolation"]["max_value"],
        }

        print(form_data,"\n\n\n")


    return render_template(f"home/macm-detailRisk.html", segment=get_segment(request),
                           macm_data=macm_data, attack_data=attack_data, pentest_phases=pentest_phases,
                           av_pentest_phases=av_pentest_phases, threat_data=threat_data,
                           methodologies_data=methodologies_data, ThreatAgentParameters=ThreatAgentParameters, form_data=form_data)

@blueprint.route('/save_risk_evaluation', methods=['GET'])
def save_risk_evaluation():


    return render_template(f"home/macmRisk.html", segment=get_segment(request))


def reverse_map_stride(input_data):
    # Reverse mapping dictionary
    reverse_stride_mapping = {
        "S": "spoofing",
        "T": "tampering",
        "R": "reputation",
        "I": "informationdisclosure",
        "D": "dos",
        "E": "elevationofprivileges",
        "STRIDE": ["spoofing", "tampering", "reputation", "informationdisclosure", "dos", "elevationofprivileges"],
        "NONE": "None",
    }

    # Normalize input: Handle both single and comma-separated inputs
    if isinstance(input_data, str):
        abbreviations = input_data.strip().upper().split(",")
    else:
        return ["Unknown"]  # If input is not a string

    # Initialize an empty list for the mapped terms
    mapped_terms = []

    for abbr in abbreviations:
        # Handle the "STRIDE" case by extending the list with all STRIDE elements
        term = reverse_stride_mapping.get(abbr.strip(), "Unknown")
        if abbr.strip() == "STRIDE" and isinstance(term, list):
            mapped_terms.extend(term)  # Add all STRIDE elements
        elif term != "Unknown":
            mapped_terms.append(term)  # Add regular mappings

    return mapped_terms

def map_stride(input_data):
    # Reverse mapping dictionary for STRIDE
    reverse_stride_mapping = {
        "S": "Spoofing",
        "T": "Tampering",
        "R": "Repudiation",
        "I": "Information Disclosure",
        "D": "Denial of Service (DoS)",
        "E": "Elevation of Privileges",
        "STRIDE": ["Spoofing", "Tampering", "Repudiation", "Information Disclosure", "Denial of Service (DoS)", "Elevation of Privileges"],
        "NONE": "None",
    }

    # Normalize input: Handle both single and comma-separated inputs
    if isinstance(input_data, str):
        abbreviations = input_data.strip().upper().split(",")
    else:
        return "Unknown"  # If input is not a string, return "Unknown"

    # Initialize an empty list for the mapped terms
    mapped_terms = []

    for abbr in abbreviations:
        # Handle the "STRIDE" case by extending the list with all STRIDE elements
        term = reverse_stride_mapping.get(abbr.strip(), "Unknown")
        if abbr.strip() == "STRIDE" and isinstance(term, list):
            mapped_terms.extend(term)  # Add all STRIDE elements
        elif term != "Unknown":
            mapped_terms.append(term)  # Add regular mappings

    # Join the terms into a single string
    return ", ".join(mapped_terms)



